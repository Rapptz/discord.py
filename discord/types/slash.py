from typing import List, Optional
class SlashChoice:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value
class SlashOption:
    def __init__(self, name: str, description: str, type_: int, required: bool, choices: Optional[List[SlashChoice]]):
        self.name = name
        self.description = description
        self.type = type_
        self.required = required
        if self.type == 3:
            # We should have choices if type is 3
            try:
                self.choices = choices
            except:
                raise Exception("You need choices for this option")
        else:
            self.choices = None
        
