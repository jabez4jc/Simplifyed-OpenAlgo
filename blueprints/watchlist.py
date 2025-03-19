from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for, abort
from utils.session import check_session_validity, is_session_valid
from database.watchlist_db import (
    create_watchlist, get_watchlist, get_user_watchlists, delete_watchlist,
    add_watchlist_item, remove_watchlist_item, get_strategy_symbols, get_user_strategy_symbols
)
import logging

logger = logging.getLogger(__name__)

watchlist_bp = Blueprint('watchlist_bp', __name__, url_prefix='/watchlist')

@watchlist_bp.route('/')
@check_session_validity
def index():
    """Display the watchlist dashboard"""
    # Get user ID from session
    user_id = session.get('user')
    
    # Get all strategy symbols for this user
    strategy_symbols = get_user_strategy_symbols(user_id)
    
    # Group symbols by strategy
    strategies = {}
    for item in strategy_symbols:
        strategy_id = item['strategy_id']
        if strategy_id not in strategies:
            strategies[strategy_id] = {
                'name': item['strategy_name'],
                'id': strategy_id,
                'is_active': item['is_active'],
                'trading_mode': item['trading_mode'],
                'is_intraday': item['is_intraday'],
                'start_time': item['start_time'],
                'end_time': item['end_time'],
                'squareoff_time': item['squareoff_time'],
                'symbols': []
            }
        strategies[strategy_id]['symbols'].append({
            'symbol': item['symbol'],
            'exchange': item['exchange'],
            'quantity': item['quantity'],
            'product_type': item['product_type']
        })
    
    # Get user watchlists
    watchlists = get_user_watchlists(user_id)
    
    return render_template(
        'watchlist/index.html',
        strategies=strategies.values(),
        watchlists=watchlists,
        strategy_symbols=strategy_symbols
    )

@watchlist_bp.route('/create', methods=['POST'])
@check_session_validity
def create():
    """Create a new watchlist"""
    user_id = session.get('user')
    name = request.form.get('name')
    
    if not name:
        flash('Watchlist name is required', 'error')
        return redirect(url_for('watchlist_bp.index'))
    
    # Create the watchlist
    watchlist = create_watchlist(name, user_id)
    
    if watchlist:
        flash(f'Watchlist "{name}" created successfully', 'success')
    else:
        flash('Failed to create watchlist', 'error')
    
    return redirect(url_for('watchlist_bp.index'))

@watchlist_bp.route('/<int:watchlist_id>/delete', methods=['POST'])
@check_session_validity
def delete(watchlist_id):
    """Delete a watchlist"""
    user_id = session.get('user')
    
    # Get the watchlist
    watchlist = get_watchlist(watchlist_id)
    
    # Check if watchlist exists and belongs to user
    if not watchlist or watchlist.user_id != user_id:
        flash('Watchlist not found', 'error')
        return redirect(url_for('watchlist_bp.index'))
    
    # Delete the watchlist
    if delete_watchlist(watchlist_id):
        flash(f'Watchlist "{watchlist.name}" deleted successfully', 'success')
    else:
        flash('Failed to delete watchlist', 'error')
    
    return redirect(url_for('watchlist_bp.index'))

@watchlist_bp.route('/<int:watchlist_id>/add_item', methods=['POST'])
@check_session_validity
def add_item(watchlist_id):
    """Add an item to a watchlist"""
    user_id = session.get('user')
    
    # Get the watchlist
    watchlist = get_watchlist(watchlist_id)
    
    # Check if watchlist exists and belongs to user
    if not watchlist or watchlist.user_id != user_id:
        return jsonify({'success': False, 'message': 'Watchlist not found'}), 404
    
    # Get form data
    symbol = request.form.get('symbol')
    exchange = request.form.get('exchange')
    notes = request.form.get('notes')
    
    if not symbol or not exchange:
        return jsonify({'success': False, 'message': 'Symbol and exchange are required'}), 400
    
    # Add the item
    item = add_watchlist_item(watchlist_id, symbol, exchange, notes)
    
    if item:
        return jsonify({
            'success': True, 
            'message': 'Item added successfully',
            'item': {
                'id': item.id,
                'symbol': item.symbol,
                'exchange': item.exchange,
                'notes': item.notes
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Failed to add item'}), 500

@watchlist_bp.route('/item/<int:item_id>/remove', methods=['POST'])
@check_session_validity
def remove_item(item_id):
    """Remove an item from a watchlist"""
    # Remove the item
    if remove_watchlist_item(item_id):
        return jsonify({'success': True, 'message': 'Item removed successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to remove item'}), 500

@watchlist_bp.route('/strategy_symbols')
@check_session_validity
def strategy_symbols():
    """Get all strategy symbols for the user"""
    user_id = session.get('user')
    symbols = get_user_strategy_symbols(user_id)
    return jsonify(symbols)

@watchlist_bp.route('/strategy/<int:strategy_id>/symbols')
@check_session_validity
def strategy_details(strategy_id):
    """Get symbols for a specific strategy"""
    user_id = session.get('user')
    all_symbols = get_user_strategy_symbols(user_id)
    
    # Filter by strategy ID
    symbols = [s for s in all_symbols if s['strategy_id'] == strategy_id]
    
    if not symbols:
        return jsonify({'success': False, 'message': 'Strategy not found or no symbols configured'}), 404
    
    return jsonify({
        'success': True,
        'strategy_name': symbols[0]['strategy_name'],
        'symbols': symbols
    }) 