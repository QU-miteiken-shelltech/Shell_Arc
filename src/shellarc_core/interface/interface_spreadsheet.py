from typing import Protocol, runtime_checkable


@runtime_checkable
class Interface_Spreadsheet(Protocol):
    """Protocol interface for Google Spreadsheet IO operations.
    """

    def get_info(self,
                 info_type: str,
                 cut_num: int,
                 page_idx: int = 0
                 ) -> str | None:
        """Get the specified information from the Google Spreadsheet.

        Args:
            info_type (str): The type of information to retrieve (e.g., "status", "assigned_person").
            cut_num (int): The cut number of the component.
            page_idx (int): The index of the spreadsheet page (Default : 0).

        Returns:
            str | None: The retrieved information, or None if the cell is empty.
        """
        ...

    def update_info(self,
                    info_type: str,
                    cut_num: int,
                    new_value: str,
                    page_idx: int = 0
                    ) -> None:
        """Update the specified information in the Google Spreadsheet.

        Args:
            info_type (str): The type of information to update.
            cut_num (int): The cut number of the component.
            new_value (str): The new value to set.
            page_idx (int): The index of the spreadsheet page (Default : 0).
        """
        ...

    def color_cell(self,
                   info_type: str,
                   cut_num: int,
                   target_color: tuple[float],
                   page_idx: int = 0
                   ) -> None:
        """Color a specific cell in the Google Spreadsheet.

        Args:
            info_type (str): The type of information corresponding to the cell.
            cut_num (int): The cut number of the component.
            target_color (tuple[float]): RGB color values (each between 0 and 1).
            page_idx (int): The index of the spreadsheet page (Default : 0).
        """
        ...

    @property
    def spreadsheet_cache(self) -> list:
        """Get the cached values of the spreadsheet page.

        Returns:
            list: A list of lists representing the cached values.
        """
        ...
