from peewee import (
    Model, CharField, TextField, IntegerField, ForeignKeyField, 
    DateTimeField, BooleanField, AutoField, SQL, EnumField
)
from playhouse.postgres_ext import PostgresqlExtDatabase

db = PostgresqlExtDatabase('feedly_trend')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = AutoField()
    name = CharField(max_length=255)
    email = CharField(max_length=255, unique=True)
    password_hash = TextField()
    role = EnumField(choices=['user', 'admin'], default='user')
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Feed(BaseModel):
    id = AutoField()
    title = CharField(max_length=255)
    url = TextField(unique=True)
    description = TextField(null=True)
    language = CharField(max_length=50, null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Article(BaseModel):
    id = AutoField()
    feed = ForeignKeyField(Feed, backref='articles', on_delete='CASCADE')
    title = CharField(max_length=255)
    summary = TextField(null=True)
    content = TextField(null=True)
    url = TextField(unique=True)
    author = CharField(max_length=255, null=True)
    published_at = DateTimeField(null=True)
    fetched_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Category(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='categories', on_delete='CASCADE')
    name = CharField(max_length=255)
    description = TextField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Subscription(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='subscriptions', on_delete='CASCADE')
    feed = ForeignKeyField(Feed, backref='subscriptions', on_delete='CASCADE')
    category = ForeignKeyField(Category, backref='subscriptions', null=True, on_delete='SET NULL')
    subscribed_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class UserInteraction(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='interactions', on_delete='CASCADE')
    article = ForeignKeyField(Article, backref='interactions', on_delete='CASCADE')
    status = EnumField(choices=['unread', 'read'], default='unread')
    is_favorite = BooleanField(default=False)
    is_saved = BooleanField(default=False)
    interacted_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Notification(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='notifications', on_delete='CASCADE')
    message = TextField()
    is_read = BooleanField(default=False)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Setting(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='settings', on_delete='CASCADE')
    theme = EnumField(choices=['light', 'dark'], default='light')
    language = CharField(max_length=50, default='en')
    notifications_enabled = BooleanField(default=True)
