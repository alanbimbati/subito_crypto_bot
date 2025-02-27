from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Table, text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import (Integer, String, ForeignKey, Text, Boolean)
import random
import math

Base = declarative_base()
db_name = 'subito_crypto.db'


def genera_livelli(num_livelli):
    livelli = []
    base = 100  # Esperienza per il primo livello
    incremento = 100  # Incremento iniziale

    for i in range(num_livelli):
        if i == 0:
            livelli.append(0)  # Livello 0
        else:
            # Calcola l'esperienza necessaria per il livello i
            exp = int(base + incremento * (i ** 1.5))  # Utilizza una funzione polinomiale
            livelli.append(exp)

            # Aumenta l'incremento in modo controllato
            if i < 10:
                incremento += 1  # Aumenta più rapidamente nei primi livelli
            else:
                incremento += 2  # Stabilizza l'incremento dopo il decimo livello

    return livelli


livelli = genera_livelli(150)

# for index,lv in enumerate(livelli):
#     print(f"lv {index}: {livelli[index]}")

# Tabella di associazione per la relazione molti-a-molti tra Utente e Group
utente_group_association = Table('utente_group_association', Base.metadata,
                                  Column('utente_id', Integer, ForeignKey('utente.id')),
                                  Column('group_id', Integer, ForeignKey('group.id'))
                                  )


class Database:
    def __init__(self):
        self.engine = create_engine(f'sqlite:///{db_name}')
        Base.metadata.create_all(self.engine)  # Create tables if they don't exist
        self.Session = sessionmaker(bind=self.engine)

    def add_pgp_key_column_if_not_exists(self):
        """Adds the pgp_key column to the utente table if it doesn't exist."""
        conn = self.engine.connect()
        try:
            # Check if the column exists
            result = conn.execute(
                text("PRAGMA table_info(utente)")
            ).fetchall()
            column_exists = False
            for row in result:
                if row[1] == 'pgp_key':
                    column_exists = True
                    break

            # Add the column if it doesn't exist
            if not column_exists:
                conn.execute(text("ALTER TABLE utente ADD COLUMN pgp_key TEXT"))
                conn.commit()
                print("Added pgp_key column to utente table.")
            else:
                print("pgp_key column already exists in utente table.")

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


class Utente(Base):
    __tablename__ = "utente"
    id = Column(Integer, primary_key=True)
    id_telegram = Column('id_Telegram', Integer, unique=True)
    nome = Column('nome', String(32))
    cognome = Column('cognome', String(32))
    username = Column('username', String(32), unique=True)
    exp = Column('exp', Integer)
    trustscore = Column('trustscore', Integer)
    livello = Column('livello', Integer)
    admin = Column('admin', Integer)
    pgp_key = Column('pgp_key', Text, nullable=True)
    groups = relationship("Group", secondary=utente_group_association, back_populates="utenti")

    def CreateUser(self, id_telegram, username, name, last_name):
        session = Database().Session()
        user = session.query(Utente).filter_by(id_telegram=id_telegram).first()
        if user is None:
            try:
                utente = Utente()
                utente.username = username
                utente.nome = name
                utente.id_telegram = id_telegram
                utente.cognome = last_name
                utente.exp = 0
                utente.livello = 1
                utente.trustscore = 0
                utente.admin = 0
                utente.pgp_key = None
                session.add(utente)
                session.commit()
            except:
                session.rollback()
                raise
            finally:
                session.close()
        elif user.username != username:
            self.update_user(id_telegram, {'username': username, 'nome': name, 'cognome': last_name})
        return user

    def getUtente(self, target):
        utente = None
        target = str(target)
        session = Database().Session()

        try:
            if target.startswith('@'):
                utente = session.query(Utente).filter_by(username=target).first()
            else:
                chatid = int(target) if target.isdigit() else None
                if chatid is not None:
                    utente = session.query(Utente).filter_by(id_telegram=chatid).first()
        finally:
            session.close()

        return utente

    def getUtenteByMessage(self, message):
        if message.chat.type == "group" or message.chat.type == "supergroup":
            chatid = message.from_user.id
        elif message.chat.type == 'private':
            chatid = message.chat.id
        return self.getUtente(chatid)

    def addUserToGroup(self, user, group_id, group_name):
        session = Database().Session()
        try:
            group = session.query(Group).filter_by(id_telegram=group_id).first()

            # Se il gruppo non esiste, lo creiamo
            if not group:
                group = Group(name=group_name, id_telegram=group_id)
                session.add(group)
                session.commit()

            # Ricarichiamo l'oggetto user nella sessione corrente
            user = session.merge(user)
            group = session.merge(group)

            if group not in user.groups:
                user.groups.append(group)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def registerUser(self, message):
        chatid = message.from_user.id
        username = '@' + message.from_user.username
        name = message.from_user.first_name
        last_name = message.from_user.last_name
        user = self.CreateUser(id_telegram=chatid, username=username, name=name, last_name=last_name)
        if message.chat.type in ["group", "supergroup"]:
            self.addUserToGroup(user, message.chat.id, message.chat.title)

    def deleteUser(self, user_id):
        session = Database().Session()
        try:
            # Cerca l'utente usando l'id Telegram
            user = session.query(Utente).filter_by(id_telegram=user_id).first()
            if user is None:
                return False  # Utente non trovato
            session.delete(user)
            session.commit()
            return True  # Eliminazione avvenuta con successo
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def isAdmin(self, utente):
        session = Database().Session()
        try:
            if utente:
                exist = session.query(Utente).filter_by(id_telegram=utente.id_telegram, admin=1).first()
                return False if exist is None else True
            else:
                return False
        finally:
            session.close()

    def infoUser(self, utente):
        nome_utente = utente.nome if utente.username is None else utente.username
        exp_to_lv = livelli[utente.livello]
        answer = ""
        answer += f"*👤 {nome_utente}*\n"
        answer += f"*🤝 Trust Score*: {utente.trustscore}\n"
        answer += f"*💪🏻 Exp*: {utente.exp}/{exp_to_lv}\n"
        answer += f"*🎖 Lv. *{utente.livello}\n"
        if utente.pgp_key:
            answer += f"*🔑 PGP Key*: `{(utente.pgp_key)[:20]}...`\n"
        return answer

    def addRandomExp(self):
        exp = random.randint(1, 5)
        self.addExp(exp)

    def addExp(self, exp):
        exp_to_lv = livelli[self.livello]
        newexp = self.exp + exp
        if newexp >= exp_to_lv:
            newlv = self.livello + 1
        else:
            newlv = self.livello
        self.update_user(self.id_telegram, {'exp': newexp, 'livello': newlv})

    def update_table_entry(self, table_class, filter_column, filter_value, update_dict):
        session = Database().Session()
        try:
            table_entry = session.query(table_class).filter_by(**{filter_column: filter_value}).first()
            for key, value in update_dict.items():
                setattr(table_entry, key, value)
            session.commit()
        finally:
            session.close()

    def update_user(self, chatid, kwargs):
        self.update_table_entry(Utente, "id_telegram", chatid, kwargs)

    def set_pgp_key(self, user_id, pgp_key):
        """Sets the PGP key for a user."""
        session = Database().Session()
        try:
            user = session.query(Utente).filter_by(id_telegram=user_id).first()
            if user:
                user.pgp_key = pgp_key
                session.commit()
                return True
            else:
                return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    id_telegram = Column('id_Telegram', Integer, unique=True)
    positivo = Column('positivo', Integer)
    commento = Column('commento', Text)

    def createFeedback(self, id_telegram, positivo, commento):
        session = Database().Session()
        feedback = Feedback(id_telegram=id_telegram, positivo=positivo, commento=commento)
        session.add(feedback)
        session.commit()
        session.close()
        return feedback

    def getFeedbacks(self, id_telegram):
        session = Database().Session()
        feedback = session.query(Feedback).filter_by(id_telegram=id_telegram).all()
        session.close()
        return feedback


class Group(Base):
    __tablename__ = "group"
    id = Column(Integer, primary_key=True)
    name = Column('name', String(64))
    id_telegram = Column('id_telegram', String(64), unique=True)
    official = Column('official', Boolean, default=False)  # Indica se il gruppo è ufficiale
    utenti = relationship("Utente", secondary=utente_group_association, back_populates="groups")

    def createGroup(self, id_telegram, name):
        session = Database().Session()
        group = session.query(Group).filter_by(name=name).first()
        if group is None:
            group = Group(
                id_telegram=id_telegram,
                name=name
            )
            session.add(group)
            session.commit()
        session.close()
        return group

    def getGroup(self, name):
        session = Database().Session()
        group = session.query(Group).filter_by(name=name).first()
        session.close()
        return group

    @classmethod
    def officialize(cls, id_telegram, admin_id):
        """
        Rende ufficiale un gruppo. Solo un utente admin (admin == 1) può ufficializzare un gruppo.
        """
        session = Database().Session()
        try:
            group = session.query(cls).filter_by(id_telegram=str(id_telegram)).first()
            if not group:
                raise Exception("Gruppo non trovato")
            admin = session.query(Utente).filter_by(id_telegram=admin_id, admin=1).first()
            if not admin:
                raise Exception("Non autorizzato: solo un admin può ufficializzare il gruppo")
            group.official = True
            session.commit()
            return group
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
