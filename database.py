from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import ForeignKey

Base = declarative_base()


class WebSites(Base):
    __tablename__ = 'websites'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    title = Column(String)
    parsed = Column(Boolean, default=False)


class Links(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('websites.id'))
    link = Column(String)
