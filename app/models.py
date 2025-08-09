from datetime import datetime
from typing import (
    Optional,
    Dict,
    Any,
    List,
)
import uuid

from sqlalchemy import (
    Column,
    Integer,
    SmallInteger,
    String,
    Text,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    Table,
    desc,
    select,
    func,
    UUID,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import (
    relationship,
    backref,
    validates,
    Mapped,
    mapped_column,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.database import (
    Base,
    session,
)
from flask_login import (
    UserMixin,
    current_user,
)
# Mapped[Optional[str]] 會自動設定 nullable=True
# nickname: Mapped[Optional[str]]


class TimestampMixin(object):
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class SourceMixin(object):
    # key: Mapped[uuid.UUID] = mapped_column(
    #     UUID(as_uuid=True),
    #     default=uuid.uuid4
    # )
    #version: Mapped[int] = mapped_column(default=1)
    source_id = mapped_column(Integer)
    source_name = mapped_column(String(500))
    source_data: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class WebhookEvent(Base, TimestampMixin):
    __tablename__ = 'webhook_event'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB)


class Notification(Base, TimestampMixin):
    __tablename__ = 'notification'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    content: Mapped[Optional[str]] = mapped_column(Text)
    event_id: Mapped[int] = mapped_column(ForeignKey('webhook_event.id'))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

class Publication(Base, TimestampMixin):
    __tablename__ = 'publication'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str] = mapped_column(String(500))
    literatures: Mapped[List['PublicationLiterature']] = relationship(back_populates='publication')


class PublicationLiterature(Base, TimestampMixin, SourceMixin):
    # TaiCOL ref
    __tablename__ = 'publication_literature'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    publication_id: Mapped[int] = mapped_column(ForeignKey('publication.id'))

    publication: Mapped[Publication] = relationship(back_populates='literatures')

class Collection(Base, SourceMixin):
    # TaiCOL namespace
    __tablename__ = 'collection'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))


class Item(Base, TimestampMixin, SourceMixin):
    # TaiCOL namespace name
    __tablename__ = 'item'

    id: Mapped[int] = mapped_column(primary_key=True)
    scientific_name: Mapped[str] = mapped_column(String(500))
    common_names: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    collection_id: Mapped[int] = mapped_column(ForeignKey('collection.id'))

    synonyms: Mapped[List['ItemSynonym']] = relationship(back_populates='item')
    specimens: Mapped[List['ItemSpecimen']] = relationship(back_populates='item')
    distributions: Mapped[List['ItemDistribution']] = relationship(back_populates='item')


class ItemSynonym(Base):
    __tablename__ = 'item_synonym'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    ref: Mapped[str] = mapped_column(String(500))
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id'))
    item: Mapped[Item] = relationship(back_populates='synonyms')

class ItemSpecimen(Base, SourceMixin):
    __tablename__ = 'item_specimen'

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(500))
    named_area_id: Mapped[int] = mapped_column(ForeignKey('named_area.id'))
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id'))
    item: Mapped[Item] = relationship(back_populates='specimens')

class ItemDistribution(Base):
    __tablename__ = 'item_distribution'

    id: Mapped[int] = mapped_column(primary_key=True)
    sequence: Mapped[int] = mapped_column(Integer)
    item_specimen_id: Mapped[int] = mapped_column(ForeignKey('item_specimen.id'))
    named_area_id: Mapped[int] = mapped_column(ForeignKey('named_area.id'))
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id'))
    item: Mapped[Item] = relationship(back_populates='distributions')

class NamedArea(Base):
    __tablename__ = 'named_area'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    tw_post_id: Mapped[str] = mapped_column(String(500))
    #area_class_id: Mapped[str] = mapped_column(Integer)
    area_class: Mapped[str] = mapped_column(String(500)) # county, stateProvince, country


class User(Base, TimestampMixin, UserMixin):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(500))
    email: Mapped[str] = mapped_column(String(500))
    passwd: Mapped[str] = mapped_column(String(500))
