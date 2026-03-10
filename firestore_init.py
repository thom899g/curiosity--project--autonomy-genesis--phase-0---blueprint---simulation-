"""
Initialize Firestore with the Autonomy Genesis schema.
This must be run first to create collections and the constitution.
"""
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_firestore() -> firestore.Client:
    """Initialize Firestore client with emulator support."""
    try:
        # Check for emulator environment variable
        emulator_host = Path('.env').read_text().split('FIRESTORE_EMULATOR_HOST=')[-1].split('\n')[0] if Path('.env').exists() else None
        
        if not firebase_admin._apps:
            if emulator_host and 'localhost' in emulator_host:
                # Use emulator with default project
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {
                    'projectId': 'autonomy-genesis-sim'
                })
                logger.info(f"Initialized Firestore emulator at {emulator_host}")
            else:
                # Use service account credentials
                cred_path = Path('.env').read_text().split('GOOGLE_APPLICATION_CREDENTIALS=')[-1].split('\n')[0]
                cred = credentials.Certificate(cred_path.strip())
                firebase_admin.initialize_app(cred)
                logger.info("Initialized Firestore with service account")
        
        return firestore.client()
    except Exception as e:
        logger.error(f"Firestore initialization failed: {e}")
        sys.exit(1)

def create_constitution(db: firestore.Client) -> None:
    """Create the immutable constitution document."""
    constitution_ref = db.collection('system').document('constitution')
    
    constitution = {
        'version': '1.0',
        'created_at': firestore.SERVER_TIMESTAMP,
        'immutable_rules': {
            'max_capital_concentration': 0.3,  # No single agent >30%
            'minimum_performance_threshold': 0.01,  # 1% return to qualify for capital
            'failsafe_approval_required': True,
            'max_leverage': 3.0,
            'max_drawdown_limit': 0.25,
            'genetic_diversity_minimum': 5,  # Minimum unique strategies
        },
        'economic_parameters': {
            'capital_allocation_interval_hours': 24,
            'prediction_market_fee': 0.001,
            'agent_birth_cost': 100.0,
            'agent_maintenance_cost': 1.0,
        },
        'meta_rules': {
            'constitution_amendment_threshold': 0.95,  # 95% agent consensus required
            'emergency_shutdown_condition': 'three_consecutive_quarterly_losses'
        }
    }
    
    try:
        constitution_ref.set(constitution)
        logger.info("Constitution document created successfully")
    except Exception as e:
        logger.error(f"Failed to create constitution: {e}")

def create_collections(db: firestore.Client) -> None:
    """Create all required collections with initial documents."""
    collections = [
        ('system', ['constitution', 'treasury']),
        ('candidate_agents', []),
        ('active_agents', []),
        ('strategy_bank', []),
        ('prediction_market', ['order_book', 'resolved_markets']),
        ('market_research', []),
        ('audit_log', []),
        ('failsafe_votes', []),
    ]
    
    for collection_name, initial_docs in collections:
        try:
            # Just create a test document to ensure collection exists
            if initial_docs:
                for doc_name in initial_docs:
                    db.collection(collection_name).document(doc_name).set({'initialized': True})
            else:
                db.collection(collection_name).document('_placeholder').set({'initialized': True})
            logger.info(f"Collection '{collection_name}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize collection '{collection_name}': {e}")
    
    # Initialize treasury
    treasury_ref = db.collection('system').document('treasury')
    treasury_ref.set({
        'balance': 10000.0,  # Initial simulated capital
        'currency': 'sim_USD',
        'last_allocated': firestore.SERVER_TIMESTAMP,
        'allocation_history': []
    })

def seed_initial_strategies(db: firestore.Client) -> None:
    """Seed the strategy bank with basic trading strategies."""
    strategies = [
        {
            'id': 'MA_CROSS_001',
            'genome': {
                'type': 'moving_average_crossover',
                'params': {'fast_period': 10, 'slow_period': 30},
                'entry_condition': 'fast_above_slow',
                'exit_condition': 'fast_below_slow'
            },
            'metadata': {
                'created_at': firestore.SERVER_TIMESTAMP,
                'complexity_score': 1.0,
                'risk_category': 'medium'
            }
        },
        {
            'id': 'MEAN_REVERSION_001',
            'genome': {
                'type': 'mean_reversion',
                'params': {'lookback_period': 20, 'std_dev_threshold': 2.0},
                'entry_condition': 'price_below_band',
                'exit_condition': 'price_above_mean'
            },
            'metadata': {
                'created_at': firestore.SERVER_TIMESTAMP,
                'complexity_score': 1.5,
                'risk_category': 'high'
            }
        },
        {
            'id': 'MOMENTUM_001',
            'genome': {
                'type': 'momentum',
                'params': {'lookback_period': 14, 'threshold': 0.02},
                'entry_condition': 'momentum_above_threshold',
                'exit_condition': 'momentum_below_zero'
            },
            'metadata': {
                'created_at': firestore.SERVER_TIMESTAMP,
                'complexity_score': 1.2,
                'risk_category': 'medium'
            }
        }
    ]
    
    for strategy in strategies:
        try:
            db.collection('strategy_bank').document(strategy['id']).set(strategy)
            logger.info(f"Seeded strategy: {strategy['id']}")
        except Exception as e:
            logger.error(f"Failed to seed strategy {strategy['id']}: {e}")

if __name__ == "__main__":
    logger.info("Initializing Autonomy Genesis Firestore schema...")
    db = initialize_firestore()
    create_collections(db)
    create_constitution(db)
    seed_initial_strategies(db)
    logger.info("Firestore initialization complete. System ready for simulation.")