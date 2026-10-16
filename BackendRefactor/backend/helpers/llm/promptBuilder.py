import io


class Prompt:
    def __init__(self):
        self.prompt = []
        self.item_count = 0
    
    def append_item(self, item):
        # Check if item is a string or a file-like object
        if not isinstance(item, (str, io.IOBase)):
            raise ValueError(f"Can't append item of type {type(item)}. Only str or file-like objects are allowed.")
        
        self.prompt.append(item)
        self.item_count += 1

    def pop(self):
        if self.item_count <= 0:
            return
        self.prompt.pop()
        self.item_count -= 1
    
    def get_prompt_as_str(self) -> str:

        prompt = []
        for item in self.prompt:
            if isinstance(item, str):
                prompt.append(item)
            elif isinstance(item, io.IOBase):
                prompt.append(item.read())
            else:
                raise ValueError(f"Item of type {type(item)} is not supported.")
        
        return ' '.join(prompt)
