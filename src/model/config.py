from dataclasses import dataclass

@dataclass
class Config:
    input: str = 'temp/input.mp4'
    output: str = 'temp/output.mp4'