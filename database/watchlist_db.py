from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import os
import logging
from database.strategy_db import Strategy, StrategySymbolMapping, db_session as strategy_db_session
from database.chartink_db import ChartinkStrategy, ChartinkSymbolMapping, db_session as chartink_db_session

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=10
)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

class Watchlist(Base):
    """Model for user watchlists"""
    __tablename__ = 'watchlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    user_id = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    symbols = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")

class WatchlistItem(Base):
    """Model for watchlist items"""
    __tablename__ = 'watchlist_items'
    
    id = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id'), nullable=False)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(10), nullable=False)
    notes = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="symbols")

def init_db():
    """Initialize the database"""
    print("Initializing Watchlist DB")
    Base.metadata.create_all(bind=engine)

def create_watchlist(name, user_id, is_default=False):
    """Create a new watchlist"""
    try:
        watchlist = Watchlist(
            name=name,
            user_id=user_id,
            is_default=is_default
        )
        db_session.add(watchlist)
        db_session.commit()
        return watchlist
    except Exception as e:
        logger.error(f"Error creating watchlist: {str(e)}")
        db_session.rollback()
        return None

def get_watchlist(watchlist_id):
    """Get watchlist by ID"""
    try:
        return Watchlist.query.get(watchlist_id)
    except Exception as e:
        logger.error(f"Error getting watchlist {watchlist_id}: {str(e)}")
        return None

def get_user_watchlists(user_id):
    """Get all watchlists for a user"""
    try:
        return Watchlist.query.filter_by(user_id=user_id).all()
    except Exception as e:
        logger.error(f"Error getting user watchlists: {str(e)}")
        return []

def delete_watchlist(watchlist_id):
    """Delete a watchlist and its items"""
    try:
        watchlist = get_watchlist(watchlist_id)
        if watchlist:
            db_session.delete(watchlist)
            db_session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting watchlist: {str(e)}")
        db_session.rollback()
        return False

def add_watchlist_item(watchlist_id, symbol, exchange, notes=None):
    """Add an item to a watchlist"""
    try:
        item = WatchlistItem(
            watchlist_id=watchlist_id,
            symbol=symbol,
            exchange=exchange,
            notes=notes
        )
        db_session.add(item)
        db_session.commit()
        return item
    except Exception as e:
        logger.error(f"Error adding watchlist item: {str(e)}")
        db_session.rollback()
        return None

def remove_watchlist_item(item_id):
    """Remove an item from a watchlist"""
    try:
        item = WatchlistItem.query.get(item_id)
        if item:
            db_session.delete(item)
            db_session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error removing watchlist item: {str(e)}")
        db_session.rollback()
        return False

def get_strategy_symbols():
    """Get all symbol mappings across all strategies with strategy details"""
    try:
        # Get regular strategy symbols
        regular_results = strategy_db_session.query(
            StrategySymbolMapping,
            Strategy
        ).join(
            Strategy, 
            StrategySymbolMapping.strategy_id == Strategy.id
        ).all()
        
        # Get Chartink strategy symbols
        chartink_results = chartink_db_session.query(
            ChartinkSymbolMapping,
            ChartinkStrategy
        ).join(
            ChartinkStrategy,
            ChartinkSymbolMapping.strategy_id == ChartinkStrategy.id
        ).all()
        
        # Format the results
        formatted_results = []
        
        # Format regular strategy results
        for mapping, strategy in regular_results:
            formatted_results.append({
                'symbol': mapping.symbol,
                'exchange': mapping.exchange,
                'quantity': mapping.quantity,
                'product_type': mapping.product_type,
                'strategy_name': strategy.name,
                'strategy_id': strategy.id,
                'is_active': strategy.is_active,
                'trading_mode': strategy.trading_mode,
                'is_intraday': strategy.is_intraday,
                'start_time': strategy.start_time,
                'end_time': strategy.end_time,
                'squareoff_time': strategy.squareoff_time,
                'platform': 'tradingview'
            })
        
        # Format Chartink strategy results
        for mapping, strategy in chartink_results:
            formatted_results.append({
                'symbol': mapping.chartink_symbol,
                'exchange': mapping.exchange,
                'quantity': mapping.quantity,
                'product_type': mapping.product_type,
                'strategy_name': strategy.name,
                'strategy_id': strategy.id,
                'is_active': strategy.is_active,
                'trading_mode': 'BOTH',  # Chartink strategies support both LONG and SHORT
                'is_intraday': strategy.is_intraday,
                'start_time': strategy.start_time,
                'end_time': strategy.end_time,
                'squareoff_time': strategy.squareoff_time,
                'platform': 'chartink'
            })
        
        return formatted_results
    except Exception as e:
        logger.error(f"Error getting strategy symbols: {str(e)}")
        return []

def get_user_strategy_symbols(user_id):
    """Get all symbol mappings for a user's strategies with strategy details"""
    try:
        # Get regular strategy symbols for the user
        regular_results = strategy_db_session.query(
            StrategySymbolMapping,
            Strategy
        ).join(
            Strategy, 
            StrategySymbolMapping.strategy_id == Strategy.id
        ).filter(
            Strategy.user_id == user_id
        ).all()
        
        # Get Chartink strategy symbols for the user
        chartink_results = chartink_db_session.query(
            ChartinkSymbolMapping,
            ChartinkStrategy
        ).join(
            ChartinkStrategy,
            ChartinkSymbolMapping.strategy_id == ChartinkStrategy.id
        ).filter(
            ChartinkStrategy.user_id == user_id
        ).all()
        
        # Format the results
        formatted_results = []
        
        # Format regular strategy results
        for mapping, strategy in regular_results:
            formatted_results.append({
                'symbol': mapping.symbol,
                'exchange': mapping.exchange,
                'quantity': mapping.quantity,
                'product_type': mapping.product_type,
                'strategy_name': strategy.name,
                'strategy_id': strategy.id,
                'is_active': strategy.is_active,
                'trading_mode': strategy.trading_mode,
                'is_intraday': strategy.is_intraday,
                'start_time': strategy.start_time,
                'end_time': strategy.end_time,
                'squareoff_time': strategy.squareoff_time,
                'platform': 'tradingview'
            })
        
        # Format Chartink strategy results
        for mapping, strategy in chartink_results:
            formatted_results.append({
                'symbol': mapping.chartink_symbol,
                'exchange': mapping.exchange,
                'quantity': mapping.quantity,
                'product_type': mapping.product_type,
                'strategy_name': strategy.name,
                'strategy_id': strategy.id,
                'is_active': strategy.is_active,
                'trading_mode': 'BOTH',  # Chartink strategies support both LONG and SHORT
                'is_intraday': strategy.is_intraday,
                'start_time': strategy.start_time,
                'end_time': strategy.end_time,
                'squareoff_time': strategy.squareoff_time,
                'platform': 'chartink'
            })
        
        return formatted_results
    except Exception as e:
        logger.error(f"Error getting user strategy symbols: {str(e)}")
        return [] 