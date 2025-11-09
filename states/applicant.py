"""FSM States for applicant request flow.

Defines the state machine for users submitting access requests.
The flow guides users through providing all necessary information
for pass requests (pedestrian or vehicle).
"""
from aiogram.fsm.state import StatesGroup, State


class ApplicantStates(StatesGroup):
    """States for applicant pass request process.
    
    Flow:
        1. pass_type - Select pass type (pedestrian/vehicle)
        2. purpose - Select or enter visit purpose
        3. custom_purpose - Enter custom purpose if "Other" selected
        4. datetime - Enter requested date/time (optional)
        5. photo - Upload ID/document photo
        6. car_number - Enter vehicle registration (vehicle passes only)
    
    Example:
        await state.set_state(ApplicantStates.pass_type)
    """
    
    # Pass type selection (pedestrian/vehicle)
    pass_type = State()
    
    # Purpose of visit
    purpose = State()
    
    # Custom purpose text (if "Other" selected)
    custom_purpose = State()
    
    # Requested date and time of visit
    datetime = State()
    
    # Photo of document/ID
    photo = State()
    
    # Vehicle registration number (for vehicle passes)
    car_number = State()
