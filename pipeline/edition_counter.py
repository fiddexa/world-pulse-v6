"""
AROUND THE MAIN — Annual Edition Counter

Rules:
- four-digit edition number;
- starts at 0001 each calendar year;
- persists between process restarts;
- same edition slot receives the same number;
- a new edition receives the next number;
- January 1 starts a new annual sequence.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import tempfile


@dataclass(frozen=True)
class EditionNumber:
    year: int
    number: int

    @property
    def label(self) -> str:
        return f"EDITION {self.number:04d}"


class EditionCounter:
    """
    Persistent annual edition counter.

    Storage format:

    {
        "2026": {
            "last_number": 47,
            "slots": {
                "2026-09-01-0700": 47
            }
        }
    }
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _load(self) -> dict:
        if not self.path.exists():
            return {}

        try:
            with self.path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                data = json.load(handle)

            return (
                data
                if isinstance(data, dict)
                else {}
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Atomic replacement prevents a partially-written counter.
        fd, temporary = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=".edition_counter_",
            suffix=".tmp",
        )

        try:
            temporary_path = Path(temporary)

            with temporary_path.open(
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    data,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
                handle.write("\n")

            temporary_path.replace(
                self.path
            )

        finally:
            try:
                Path(temporary).unlink(
                    missing_ok=True
                )
            except OSError:
                pass

    def allocate(
        self,
        year: int,
        slot_key: str,
    ) -> EditionNumber:
        """
        Allocate an edition number for a unique edition slot.

        Repeating the same slot returns the previously assigned number.
        """

        if year < 1:
            raise ValueError(
                "year must be positive"
            )

        if not slot_key:
            raise ValueError(
                "slot_key must not be empty"
            )

        data = self._load()

        year_key = str(year)

        year_data = data.setdefault(
            year_key,
            {
                "last_number": 0,
                "slots": {},
            },
        )

        if not isinstance(
            year_data,
            dict,
        ):
            year_data = {
                "last_number": 0,
                "slots": {},
            }
            data[year_key] = year_data

        slots = year_data.setdefault(
            "slots",
            {},
        )

        # Same edition slot: never increment.
        existing = slots.get(slot_key)

        if existing is not None:
            number = int(existing)

            return EditionNumber(
                year=year,
                number=number,
            )

        last_number = int(
            year_data.get(
                "last_number",
                0,
            )
        )

        next_number = last_number + 1

        if next_number > 9999:
            raise RuntimeError(
                f"Edition counter exhausted for {year}"
            )

        slots[slot_key] = next_number
        year_data["last_number"] = next_number

        data[year_key] = year_data

        self._save(data)

        return EditionNumber(
            year=year,
            number=next_number,
        )

    def get(
        self,
        year: int,
        slot_key: str,
    ) -> EditionNumber | None:
        """
        Return an already assigned number without allocating one.
        """

        data = self._load()

        year_data = data.get(
            str(year)
        )

        if not isinstance(
            year_data,
            dict,
        ):
            return None

        slots = year_data.get(
            "slots",
            {},
        )

        if not isinstance(
            slots,
            dict,
        ):
            return None

        value = slots.get(
            slot_key
        )

        if value is None:
            return None

        return EditionNumber(
            year=year,
            number=int(value),
        )
