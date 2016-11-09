from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey

engine = create_engine('sqlite:///websites.db', echo=True)

Base = declarative_base()


class WebSites(Base):
    __tablename__ = 'websites'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    title = Column(String)
    bytes = Column(String)


class Links(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('websites.id'))
    url = Column(String)
    appeared_times = Column(Integer)

Base.metadata.create_all(engine)
