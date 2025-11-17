from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator, model_validator

class Memory(BaseModel):
    date: datetime = Field(alias="Date")
    download_link: Optional[str] = Field(default=None, alias="Download Link")
    media_download_url: Optional[str] = Field(default=None, alias="Media Download Url")
    media_type: str = Field(alias="Media Type")
    # Original JSON contains a Location string like: "Latitude, Longitude: 60.198174, 24.927795"
    location: Optional[str] = Field(default=None, alias="Location")
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            # Example: "2023-04-17 10:35:12 UTC"
            return datetime.strptime(v, "%Y-%m-%d %H:%M:%S UTC")
        return v

    @model_validator(mode="after")
    def _parse_location(self):
        # Try to extract lat/lon floats
        if self.location:
            m = re.search(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", self.location)
            if m:
                try:
                    self.latitude = float(m.group(1))
                    self.longitude = float(m.group(2))
                except ValueError:
                    pass
        return self

    @property
    def lat(self) -> Optional[float]:
        return self.latitude

    @property
    def lon(self) -> Optional[float]:
        return self.longitude

    @property
    def location_tuple(self) -> Optional[tuple[float, float]]:
        if self.latitude is None or self.longitude is None:
            return None
        return (self.latitude, self.longitude)

    @property
    def filename(self) -> str:
        return self.date.strftime("%Y-%m-%d_%H-%M-%S")

    @property
    def extension(self) -> str:
        return ".jpg" if self.media_type == "Image" else ".mp4"

    @property
    def preferred_url(self) -> Optional[str]:
        return self.media_download_url or self.download_link

    @property
    def filename_with_ext(self) -> str:
        return f"{self.filename}{self.extension}"
