from typing import Protocol, runtime_checkable, Callable
from pathlib import Path


@runtime_checkable
class Interface_Notion(Protocol):
    """Protocol interface for Notion IO operations.
    """

    def get_image_url(self,
                      attr_name: str = "画像"
                      ) -> str:
        """Get the image URL from Notion for the specified attribute.

        Args:
            attr_name (str): The name of the Notion property containing the image (Default : "画像").

        Returns:
            str: The image URL from Notion.
        """
        ...

    def get_image_file(self,
                       download_destination: str | Path,
                       attr_name: str = "画像"
                       ) -> None:
        """Download the image file from Notion to the specified local destination.

        Args:
            download_destination (str | Path): The local path where the downloaded image should be saved.
            attr_name (str): The name of the Notion property containing the image (Default : "画像").
        """
        ...

    def put_image_url(self,
                      img_url: str,
                      attr_name: str = "画像"
                      ) -> None:
        """Update the image URL in Notion for the specified attribute.

        Args:
            img_url (str): The image URL to set in Notion.
            attr_name (str): The name of the Notion property to update (Default : "画像").
        """
        ...


NotionFactory = Callable[[int], Interface_Notion]
"""Factory type for creating Interface_Notion instances.

Args:
    cut_num (int): The cut number to initialize the Notion IO instance with.

Returns:
    Interface_Notion: A new Notion IO instance bound to the specified cut number.

Usage:
    # Production: pass the class itself (Notion_IO.__init__ matches the signature)
    service = ShellArc_Storyboard(cut_num=1, notion_factory=Notion_IO)

    # Test: pass a lambda returning a mock
    mock_notion = MagicMock(spec=Interface_Notion)
    service = ShellArc_Storyboard(cut_num=1, notion_factory=lambda cut_num: mock_notion)
"""
