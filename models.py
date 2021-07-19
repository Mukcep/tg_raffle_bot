from re import S
from aiogram.types import message
import peewee as pw
import random
import logging
import datetime

db = pw.SqliteDatabase('bot.db')
db.connect()

class Member():
    
    def __init__(self, user_id, user_name) -> None:
        self.user_id = user_id
        self.user_name = user_name

class Raffle():
    
    def __init__(self, chat_id, name, prize, creator: Member, winners_count=1) -> None:
        self.chat_id = chat_id
        self.name = name
        self.prize = prize
        self.winners_count = winners_count
        self.creator = creator

        self.members = []
        self.winners = []
        self.stage = 'started'
        self.created = datetime.datetime.now()
        self.completed = None


    def add_member(self, member: Member):
        for m in self.members:
            if member.user_id == m.user_id:
                return False
        self.members.append(member)
        return True

    def raffle(self):
        random.shuffle(self.members)

        if int(self.winners_count) > len(self.members):
            self.winners_count = len(self.members)

        for i in range(0, int(self.winners_count)):
            self.winners.append(self.members[i])

        self.completed = datetime.datetime.now()
        self.stage = 'completed'

    def generateMessage(self):
        text = "Розыгрыш!\n"
        text += f"Автор: [{self.creator.user_name}](tg://user?id={self.creator.user_id})\n"
        text += f"Приз: {self.prize}\n"
        text += f"Призовых мест: {self.winners_count}\n"

        if len(self.members) > 0 and self.stage == 'started':
            text += f"-------\n"
            text += f"Участников: {len(self.members)}\nСписок:\n"
            for m in self.members:
                text += f"[{m.user_name}](tg://user?id={m.user_id})\n"

        if self.stage == 'completed':
            text += f"-------\n"
            text += f"Розыгрыш завершен!\n"
            text += "Победители: "
            for w in self.winners:
                text += f"[{w.user_name}](tg://user?id={w.user_id}), "
        return text

    def saveHistory(self):
        h = RaffleHistory()
        h.chat_id = int(self.chat_id)
        h.name = self.name
        h.creator = f"{self.creator.user_name}|{self.creator.user_id}"
        h.created = self.created
        h.completed = self.completed
        h.members_count = len(self.members)
        h.members = ""
        for m in self.members:
            h.members += f"{m.user_name}|{m.user_id}=="
        h.prize = self.prize
        h.winners_count = len(self.winners)
        h.winners = ""
        for w in self.winners:
            h.winners += f"{w.user_name}|{w.user_id}=="
        h.save()

class RaffleHistory(pw.Model):
    id = pw.IntegerField(index=True, primary_key=True, unique=True)
    chat_id = pw.BigIntegerField()
    name = pw.TextField()
    creator = pw.TextField()
    created = pw.DateTimeField()
    completed = pw.DateTimeField()
    members = pw.TextField()
    members_count = pw.IntegerField()
    prize = pw.TextField()
    winners_count = pw.IntegerField()
    winners = pw.TextField()

    class Meta:
        database = db # This model uses the "people.db" database.

    def generateText(self):
        creator_text = f"[{self.creator.split('|')[0]}](tg://user?id={self.creator.split('|')[1]})"

        members_text = ""
        for member in self.members.split("=="):
            if member == '': continue
            members_text += f"[{member.split('|')[0]}](tg://user?id={member.split('|')[1]}), "
        winners_text = ""
        for winner in self.winners.split("=="):
            if winner == '': continue
            winners_text += f"[{winner.split('|')[0]}](tg://user?id={winner.split('|')[1]}), "

        text = f"#—— {self.created.strftime('%Y-%m-%d')}\n"
        text += f"Автор {creator_text}\n"
        text += f"Приз: {self.prize}\n"
        text += f"Участники ({self.members_count}): {members_text}\n"
        text += f"Победители ({self.winners_count}): {winners_text}\n"
        
        # text = f"{self.created.strftime('%Y-%m-%d')} | Автор: {creator_text} | Приз: {self.prize}"
        return text

db.create_tables([RaffleHistory])

# r = models.RaffleHistory()
# r.members_count = 2
# r.chat_id = 12
# r.name = "lolkek"
# r.creator = "@maksorg"
# r.created = datetime.datetime(2021, 7, 19, 20, 0)
# r.completed = datetime.datetime(2021, 7, 19, 23, 0)
# r.members = "@maksorg, @test_member"
# r.prize = "ss"
# r.winners = "@maksorg"
# r.winners_count = 1

# r.save()