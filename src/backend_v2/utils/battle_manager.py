# -*- coding: utf-8 -*-

"""
Battle Manager for AgentBeats Backend V2.

Manages battle queue, execution, and status tracking.
"""

import asyncio
import threading
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from queue import Queue
from enum import Enum


class BattleState(str, Enum):
    """Battle state enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"
    CANCELLED = "cancelled"


class BattleManager:
    """
    Battle Manager class for handling battle queue and execution.
    
    Features:
    - Synchronous battle queue (one battle at a time)
    - Asynchronous battle execution
    - Queue position tracking
    - Battle status monitoring
    - Thread-safe operations
    """
    
    def __init__(self, battle_processor: Optional[Callable] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the Battle Manager.
        
        Args:
            battle_processor: Optional custom battle processor function
            logger: Optional logger instance
        """
        self.logger = logger or self._setup_logger()
        
        # Queue management
        self._battle_queue: Queue = Queue()
        self._queue_lock = threading.Lock()
        
        # Battle tracking
        self._battles: Dict[str, Dict[str, Any]] = {}
        self._battles_lock = threading.Lock()
        
        # Current running battle
        self._current_battle_id: Optional[str] = None
        self._current_battle_lock = threading.Lock()
        
        # Processor management
        self._battle_processor = battle_processor or self._default_battle_processor
        self._processor_thread: Optional[threading.Thread] = None
        self._processor_running = False
        self._shutdown_event = threading.Event()
        
        # Statistics
        self._total_processed = 0
        self._total_errors = 0
        
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger for battle manager."""
        logger = logging.getLogger("battle_manager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '[%(levelname)s] [%(asctime)s] BattleManager: %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False
            
        return logger
    
    def start(self) -> None:
        """Start the battle processor if not already running."""
        with self._current_battle_lock:
            if self._processor_running:
                self.logger.warning("Battle processor is already running")
                return
            
            self._processor_running = True
            self._shutdown_event.clear()
            
            self._processor_thread = threading.Thread(
                target=self._process_battle_queue,
                daemon=True,
                name="BattleProcessor"
            )
            self._processor_thread.start()
            self.logger.info("Battle processor started")
    
    def stop(self, timeout: float = 10.0) -> None:
        """
        Stop the battle processor gracefully.
        
        Args:
            timeout: Maximum time to wait for processor to stop
        """
        if not self._processor_running:
            return
            
        self.logger.info("Stopping battle processor...")
        self._shutdown_event.set()
        
        if self._processor_thread and self._processor_thread.is_alive():
            self._processor_thread.join(timeout=timeout)
            
            if self._processor_thread.is_alive():
                self.logger.warning("Battle processor did not stop gracefully within timeout")
            else:
                self.logger.info("Battle processor stopped")
        
        self._processor_running = False
    
    def add_battle(self, battle_id: str, battle_data: Dict[str, Any]) -> int:
        """
        Add a battle to the queue.
        
        Args:
            battle_id: Unique battle identifier
            battle_data: Battle configuration and metadata
            
        Returns:
            Queue position (0-based index)
        """
        with self._battles_lock:
            if battle_id in self._battles:
                raise ValueError(f"Battle {battle_id} already exists")
            
            # Create battle record
            battle_record = {
                "battle_id": battle_id,
                "state": BattleState.PENDING,
                "created_at": datetime.utcnow().isoformat() + 'Z',
                "queued_at": None,
                "started_at": None,
                "finished_at": None,
                "error": None,
                **battle_data
            }
            
            self._battles[battle_id] = battle_record
        
        # Add to queue
        with self._queue_lock:
            self._battle_queue.put(battle_id)
            queue_position = self._battle_queue.qsize() - 1
            
            # Update state to queued
            with self._battles_lock:
                self._battles[battle_id]["state"] = BattleState.QUEUED
                self._battles[battle_id]["queued_at"] = datetime.utcnow().isoformat() + 'Z'
        
        self.logger.info(f"Added battle {battle_id} to queue at position {queue_position}")
        
        # Start processor if not running
        if not self._processor_running:
            self.start()
            
        return queue_position
    
    def get_battle_status(self, battle_id: str) -> Optional[Dict[str, Any]]:
        """
        Get battle status and information.
        
        Args:
            battle_id: Battle identifier
            
        Returns:
            Battle information or None if not found
        """
        with self._battles_lock:
            battle = self._battles.get(battle_id)
            if battle:
                # Add queue position if still queued
                if battle["state"] == BattleState.QUEUED:
                    battle = battle.copy()
                    battle["queue_position"] = self.get_queue_position(battle_id)
                return battle
            return None
    
    def get_queue_position(self, battle_id: str) -> Optional[int]:
        """
        Get the queue position of a battle.
        
        Args:
            battle_id: Battle identifier
            
        Returns:
            Queue position (0-based) or None if not in queue
        """
        with self._queue_lock:
            # Convert queue to list to check position
            queue_list = list(self._battle_queue.queue)
            try:
                return queue_list.index(battle_id)
            except ValueError:
                return None
    
    def is_battle_in_queue(self, battle_id: str) -> bool:
        """
        Check if a battle is in the queue.
        
        Args:
            battle_id: Battle identifier
            
        Returns:
            True if battle is in queue, False otherwise
        """
        return self.get_queue_position(battle_id) is not None
    
    def get_current_battle(self) -> Optional[str]:
        """
        Get the currently running battle ID.
        
        Returns:
            Current battle ID or None if no battle is running
        """
        with self._current_battle_lock:
            return self._current_battle_id
    
    def get_queue_size(self) -> int:
        """
        Get the current queue size.
        
        Returns:
            Number of battles in queue
        """
        with self._queue_lock:
            return self._battle_queue.qsize()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get comprehensive queue status.
        
        Returns:
            Queue status information
        """
        with self._queue_lock, self._current_battle_lock, self._battles_lock:
            queue_list = list(self._battle_queue.queue)
            
            return {
                "queue_size": len(queue_list),
                "current_battle": self._current_battle_id,
                "processor_running": self._processor_running,
                "total_processed": self._total_processed,
                "total_errors": self._total_errors,
                "queued_battles": queue_list,
                "all_battles": {
                    battle_id: {
                        "state": battle["state"],
                        "created_at": battle["created_at"],
                        "queued_at": battle.get("queued_at"),
                        "started_at": battle.get("started_at"),
                        "finished_at": battle.get("finished_at")
                    }
                    for battle_id, battle in self._battles.items()
                }
            }
    
    def cancel_battle(self, battle_id: str) -> bool:
        """
        Cancel a battle if it's still in queue.
        
        Args:
            battle_id: Battle identifier
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        with self._battles_lock:
            battle = self._battles.get(battle_id)
            if not battle:
                return False
            
            if battle["state"] not in [BattleState.PENDING, BattleState.QUEUED]:
                self.logger.warning(f"Cannot cancel battle {battle_id} in state {battle['state']}")
                return False
        
        # Remove from queue
        with self._queue_lock:
            try:
                # Create new queue without the cancelled battle
                new_queue = Queue()
                while not self._battle_queue.empty():
                    item = self._battle_queue.get_nowait()
                    if item != battle_id:
                        new_queue.put(item)
                self._battle_queue = new_queue
                
                # Update battle state
                with self._battles_lock:
                    self._battles[battle_id]["state"] = BattleState.CANCELLED
                    self._battles[battle_id]["finished_at"] = datetime.utcnow().isoformat() + 'Z'
                
                self.logger.info(f"Cancelled battle {battle_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error cancelling battle {battle_id}: {e}")
                return False
    
    def _process_battle_queue(self) -> None:
        """Main battle queue processing loop (runs in background thread)."""
        self.logger.info("Battle queue processor started")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # Get next battle from queue (with timeout)
                    try:
                        with self._queue_lock:
                            if self._battle_queue.empty():
                                battle_id = None
                            else:
                                battle_id = self._battle_queue.get_nowait()
                    except:
                        battle_id = None
                    
                    if battle_id is None:
                        # No battles in queue, sleep and continue
                        time.sleep(1.0)
                        continue
                    
                    # Set as current battle
                    with self._current_battle_lock:
                        self._current_battle_id = battle_id
                    
                    # Update battle state
                    with self._battles_lock:
                        if battle_id in self._battles:
                            self._battles[battle_id]["state"] = BattleState.RUNNING
                            self._battles[battle_id]["started_at"] = datetime.utcnow().isoformat() + 'Z'
                    
                    self.logger.info(f"Processing battle {battle_id}")
                    
                    # Process the battle
                    try:
                        # Run battle in new event loop (since we're in a thread)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            success = loop.run_until_complete(self._run_battle_async(battle_id))
                        finally:
                            loop.close()
                        
                        # Update statistics and state
                        self._total_processed += 1
                        
                        if success:
                            final_state = BattleState.FINISHED
                            self.logger.info(f"Battle {battle_id} completed successfully")
                        else:
                            final_state = BattleState.ERROR
                            self._total_errors += 1
                            self.logger.error(f"Battle {battle_id} completed with errors")
                            
                    except Exception as e:
                        final_state = BattleState.ERROR
                        self._total_errors += 1
                        self.logger.error(f"Battle {battle_id} failed with exception: {e}")
                        
                        # Update error info
                        with self._battles_lock:
                            if battle_id in self._battles:
                                self._battles[battle_id]["error"] = str(e)
                    
                    # Update final state
                    with self._battles_lock:
                        if battle_id in self._battles:
                            self._battles[battle_id]["state"] = final_state
                            self._battles[battle_id]["finished_at"] = datetime.utcnow().isoformat() + 'Z'
                    
                    # Clear current battle
                    with self._current_battle_lock:
                        self._current_battle_id = None
                    
                except Exception as e:
                    self.logger.error(f"Error in battle queue processor: {e}")
                    time.sleep(1.0)
                    
        except Exception as e:
            self.logger.error(f"Fatal error in battle queue processor: {e}")
        finally:
            with self._current_battle_lock:
                self._current_battle_id = None
            self._processor_running = False
            self.logger.info("Battle queue processor stopped")
    
    async def _run_battle_async(self, battle_id: str) -> bool:
        """
        Run a battle asynchronously.
        
        Args:
            battle_id: Battle identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get battle data
            with self._battles_lock:
                battle_data = self._battles.get(battle_id)
                if not battle_data:
                    self.logger.error(f"Battle {battle_id} not found")
                    return False
            
            # Run the battle processor
            return await self._battle_processor(battle_id, battle_data)
            
        except Exception as e:
            self.logger.error(f"Error running battle {battle_id}: {e}")
            return False
    
    async def _default_battle_processor(self, battle_id: str, battle_data: Dict[str, Any]) -> bool:
        """
        Default battle processor (placeholder).
        
        Args:
            battle_id: Battle identifier
            battle_data: Battle configuration
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Default processor: Battle {battle_id} - sleeping for 5 seconds")
        await asyncio.sleep(5)
        self.logger.info(f"Default processor: Battle {battle_id} completed")
        return True
    
    def cleanup_old_battles(self, max_age_hours: int = 24) -> int:
        """
        Clean up old battle records.
        
        Args:
            max_age_hours: Maximum age of battles to keep
            
        Returns:
            Number of battles cleaned up
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        with self._battles_lock:
            battles_to_remove = []
            
            for battle_id, battle in self._battles.items():
                try:
                    created_time = datetime.fromisoformat(battle["created_at"].replace('Z', '+00:00')).timestamp()
                    if created_time < cutoff_time and battle["state"] in [BattleState.FINISHED, BattleState.ERROR, BattleState.CANCELLED]:
                        battles_to_remove.append(battle_id)
                except Exception as e:
                    self.logger.error(f"Error parsing time for battle {battle_id}: {e}")
            
            for battle_id in battles_to_remove:
                del self._battles[battle_id]
                cleaned_count += 1
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old battles")
            
        return cleaned_count
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
