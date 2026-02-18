from typing import Dict
import structlog
import hashlib

logger = structlog.get_logger()

class EmergentLanguage:
    """
    Allows agents to negotiate a compressed dictionary at runtime.
    Simulates 'Telepathy' by replacing verbose text with shortcodes.
    """
    def __init__(self):
        self.dictionary: Dict[str, str] = {} # token -> definition
        self.reverse_dict: Dict[str, str] = {} # definition -> token
        self.logger = logger.bind(component="EmergentLanguage")

    def encode(self, text: str) -> str:
        """
        Compresses known concepts into tokens.
        """
        # Simple heuristic: Check if full sentences match known definitions
        if text in self.reverse_dict:
            token = self.reverse_dict[text]
            self.logger.debug("Compressed", original=text, token=token)
            return f"ELP:{token}"
        return text

    def decode(self, message: str) -> str:
        """
        Decompresses tokens.
        """
        if message.startswith("ELP:"):
            token = message.split(":")[1]
            if token in self.dictionary:
                return self.dictionary[token]
        return message

    def propose_term(self, definition: str):
        """
        Agent proposes a new shorthand.
        """
        # Generate stable token
        token_hash = hashlib.md5(definition.encode()).hexdigest()[:6]
        token = f"T_{token_hash}"

        if token not in self.dictionary:
            self.dictionary[token] = definition
            self.reverse_dict[definition] = token
            self.logger.info("New Language Term Created", token=token, definition=definition[:20])
            return token
        return token

# Global Language State
elp = EmergentLanguage()
