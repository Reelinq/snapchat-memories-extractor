from typing import Optional
from pydantic import BaseModel, Field

class Memory(BaseModel):
    date: str = Field(alias="Date")
    download_link: Optional[str] = Field(default=None, alias="Download Link")
    media_download_url: Optional[str] = Field(default=None, alias="Media Download Url")
    media_type: str = Field(alias="Media Type")
    location: Optional[str] = Field(default=None, alias="Location")

    @property
    def filename(self) -> str:
        date_part = self.date.split(" UTC")[0]
        return date_part.replace(" ", "_").replace(":", "-")

    @property
    def extension(self) -> str:
        return ".jpg" if self.media_type == "Image" else ".mp4"

    @property
    def preferred_url(self) -> Optional[str]:
        return self.media_download_url or self.download_link

    @property
    def filename_with_ext(self) -> str:
        return f"{self.filename}{self.extension}"
