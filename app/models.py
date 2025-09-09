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
    key: Mapped[Optional[str]] = mapped_column(String(1000))
    source_id: Mapped[Optional[int]] = mapped_column(Integer)
    source_name: Mapped[Optional[str]] = mapped_column(String(500))
    source_data: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


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
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey('webhook_event.id'))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    event: Mapped['WebhookEvent'] = relationship()


class Publication(Base, TimestampMixin):
    __tablename__ = 'publication'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(500), default='init') # init, fetched, fetchedSpecimen
    literatures: Mapped[List['PublicationLiterature']] = relationship(back_populates='publication')
    collections: Mapped[List['Collection']] = relationship(back_populates='publication')

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
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    publication_id: Mapped[Optional[int]] = mapped_column(ForeignKey('publication.id'))

    publication: Mapped[Publication] = relationship(back_populates='collections')
    items: Mapped[List['Item']] = relationship(back_populates='collection')


class Item(Base, TimestampMixin, SourceMixin):
    # TaiCOL namespace name
    __tablename__ = 'item'

    TAICOL_RANKS = {
        "1": [
            "Domain",
            "域"
        ],
        "2": [
            "Superkingdom",
            "總界"
        ],
        "3": [
            "Kingdom",
            "界"
        ],
        "4": [
            "Subkingdom",
            "亞界"
        ],
        "5": [
            "Infrakingdom",
            "下界"
        ],
        "6": [
            "Superdivision",
            "超部|總部"
        ],
        "7": [
            "Division",
            "部|類"
        ],
        "8": [
            "Subdivision",
            "亞部|亞類"
        ],
        "9": [
            "Infradivision",
            "下部|下類"
        ],
        "10": [
            "Parvdivision",
            "小部|小類"
        ],
        "11": [
            "Superphylum",
            "超門|總門"
        ],
        "12": [
            "Phylum",
            "門"
        ],
        "13": [
            "Subphylum",
            "亞門"
        ],
        "14": [
            "Infraphylum",
            "下門"
        ],
        "15": [
            "Microphylum",
            "微門"
        ],
        "16": [
            "Parvphylum",
            "小門"
        ],
        "17": [
            "Superclass",
            "超綱|總綱"
        ],
        "18": [
            "Class",
            "綱"
        ],
        "19": [
            "Subclass",
            "亞綱"
        ],
        "20": [
            "Infraclass",
            "下綱"
        ],
        "21": [
            "Superorder",
            "超目|總目"
        ],
        "22": [
            "Order",
            "目"
        ],
        "23": [
            "Suborder",
            "亞目"
        ],
        "24": [
            "Infraorder",
            "下目"
        ],
        "25": [
            "Superfamily",
            "超科|總科"
        ],
        "26": [
            "Family",
            "科"
        ],
        "27": [
            "Subfamily",
            "亞科"
        ],
        "28": [
            "Tribe",
            "族"
        ],
        "29": [
            "Subtribe",
            "亞族"
        ],
        "30": [
            "Genus",
            "屬"
        ],
        "31": [
            "Subgenus",
            "亞屬"
        ],
        "32": [
            "Section",
            "組|節"
        ],
        "33": [
            "Subsection",
            "亞組|亞節"
        ],
        "34": [
            "Species",
            "種"
        ],
        "35": [
            "Subspecies",
            "亞種"
        ],
        "36": [
            "Nothosubspecies",
            "雜交亞種"
        ],
        "37": [
            "Variety",
            "變種"
        ],
        "38": [
            "Subvariety",
            "亞變種"
        ],
        "39": [
            "Nothovariety",
            "雜交變種"
        ],
        "40": [
            "Form",
            "型"
        ],
        "41": [
            "Subform",
            "亞型"
        ],
        "42": [
            "Special Form",
            "特別品型"
        ],
        "43": [
            "Race",
            "種族"
        ],
        "44": [
            "Stirp",
            "血統"
        ],
        "45": [
            "Morph",
            "形態型"
        ],
        "46": [
            "Aberration",
            "異常個體"
        ],
        "47": [
            "Hybrid Formula",
            "雜交組合"
        ],
        "48": [
            "Subrealm",
            "病毒亞域"
        ],
        "49": [
            "Realm",
            "病毒域"
        ],
        "50": [
            "Unranked",
            "未定義階層"
        ],
        "51": [
            "Megaclass",
            "高綱"
        ],
        "52": [
            "Grandclass",
            "大綱"
        ],
        "53": [
            "Mirclass",
            "上綱"
        ],
        "54": [
            "Epifamily",
            "領科"
        ]
    }

    COUNTY_MAP = {
        "彰化縣": "Changhua",
        "嘉義縣": "Chiayi",
        "新竹縣": "Hsinchu",
        "花蓮縣": "Hualien",
        "宜蘭縣": "Yilan",
        "金門縣": "Kinmen",
        "連江縣": "Lienchiang",
        "苗栗縣": "Miaoli",
        "南投縣": "Nantou",
        "澎湖縣": "Penghu",
        "屏東縣": "Pingtung",
        "臺東縣": "Taitung",
        "雲林縣": "Yunlin",
        "嘉義市": "Chiayi",
        "新竹市": "Hsinchu",
        "基隆市": "Keelung",
        "高雄市": "Kaohsiung",
        "新北市": "New Taipei",
        "桃園市": "Taoyuan",
        "臺南市": "Tainan",
        "臺北市": "Taipei",
        "臺中市": "Taichung"
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    scientific_name: Mapped[str] = mapped_column(String(500))
    common_names: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    distribution: Mapped[Optional[str]] = mapped_column(Text)
    note: Mapped[Optional[str]] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    collection_id: Mapped[int] = mapped_column(ForeignKey('collection.id'))

    synonyms: Mapped[List['ItemSynonym']] = relationship(back_populates='item')
    specimens: Mapped[List['ItemSpecimen']] = relationship(back_populates='item')
    distributions: Mapped[List['ItemDistribution']] = relationship(back_populates='item')

    collection: Mapped[Collection] = relationship(back_populates='items')

    def get_rank(self):
        if sd := self.source_data:
            if rank_id := sd.get('rank_id'):
                return self.TAICOL_RANKS.get(str(rank_id), ['-', '-'])

    def get_grouped_specimens(self):
        grouped = {}
        for i in self.specimens:
            if i.text:
                key = ''
                if county := i.source_data.get('county'):
                    key = county
                    if county_en := self.COUNTY_MAP.get(key, ''):
                        key = county_en.upper()
                else:
                    key = 'unsure'

                if key not in grouped:
                    grouped[key] = []

                grouped[key].append([i.id, i.text])

        return grouped

    def get_distribution_from_specimens(self):
        dist = []
        for i in self.specimens:
            d = []
            if x:= i.source_data.get('stateProvince'):
                d.append(x)
            if x:= i.source_data.get('county'):
                d.append(x)
            if x:= i.source_data.get('municipality'):
                d.append(x)

            dist.append('|'.join(d))

        return list(set(dist))

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
    text: Mapped[Optional[str]] = mapped_column(String(500))
    named_area_id: Mapped[Optional[int]] = mapped_column(ForeignKey('named_area.id'))
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
    name_zh: Mapped[str] = mapped_column(String(500))
    tw_post_id: Mapped[Optional[str]] = mapped_column(String(500))
    #area_class_id: Mapped[str] = mapped_column(Integer)
    area_class: Mapped[Optional[str]] = mapped_column(String(500)) # county, stateProvince, country


class User(Base, TimestampMixin, UserMixin):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(500))
    email: Mapped[str] = mapped_column(String(500))
    passwd: Mapped[str] = mapped_column(String(500))
    activation_token: Mapped[str] = mapped_column(String(500))
    is_activated: Mapped[bool] = mapped_column(Boolean, default=False)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    notifications: Mapped[List[Notification]] = relationship()

    def get_unread_notifications(self):
        return Notification.query.filter(Notification.user_id==self.id, Notification.read_at==None).all()
