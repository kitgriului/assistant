"""FSM States for guard operations.

Defines state machines for guard-specific functionality including
QR code validation and patrol rounds.
"""
from aiogram.fsm.state import StatesGroup, State


class GuardStates(StatesGroup):
    """States for basic guard operations.
    
    Used for QR code scanning and validation workflows.
    
    Example:
        await state.set_state(GuardStates.check_in)
    """
    
    # Waiting for QR code or pass information
    check_in = State()
    
    # Waiting for photo upload during check-in
    photo = State()


class PatrolStates(StatesGroup):
    """States for patrol round process.
    
    Manages the complete patrol workflow from start to completion,
    including checkpoint recording, photo uploads, and notes.
    
    Flow:
        1. in_patrol - Patrol session active
        2. waiting_checkpoint_action - Waiting for action at checkpoint
        3. waiting_photo - Waiting for checkpoint photo
        4. waiting_location - Waiting for GPS location (optional)
        5. waiting_notes - Waiting for checkpoint notes (optional)
    
    Example:
        await state.set_state(PatrolStates.in_patrol)
        # Guard can now record checkpoints
    """
    
    # Active patrol session in progress
    in_patrol = State()
    
    # Waiting for checkpoint action selection
    waiting_checkpoint_action = State()
    
    # Waiting for checkpoint photo upload
    waiting_photo = State()
    
    # Waiting for GPS location share (optional)
    waiting_location = State()
    
    # Waiting for checkpoint notes/comments (optional)
    waiting_notes = State()
    
    # Adding new patrol point
    adding_point = State()
    
    # Admin asking question about patrol
    asking_question = State()
    
    # Guard answering question about patrol
    answering_question = State()
    
    # Waiting for request rejection reason
    waiting_rejection_reason = State()
