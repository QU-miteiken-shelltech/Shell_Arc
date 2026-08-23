from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.exception.user_exception import SA_EditingRejection

class ShellArc_Register:
    def __init__(self):
        self.gcp_io = GCP_IO()


    async def register_work(self,
                      registering_person: str,
                      registering_component: str,
                      registering_cut: int,
                      force: bool=False
                      ) -> None:
        """Register a person for a specific component and cut in the Google Spreadsheet, with an option to force the registration even if there is already a registered person.

        Args:
            registering_person (str): The name of the person to be registered for the specified component and cut.
            registering_component (str): The name of the component to register the person for (e.g., "modeling", "texturing").
            registering_cut (int): The cut number of the component to register the person for.
            force (bool): A boolean flag indicating whether to force the registration even if there is already a registered person for the specified component and cut (Default : False).
        """
        current_pic = self.gcp_io.get_info(
            info_type=f"{registering_component}_PIC",
            cut_num=registering_cut
        )
        if current_pic and not force:
            raise SA_EditingRejection(
                error_log=f"When {registering_person} registering for c{registering_cut} {registering_component}, " \
                    f"overwritting rejected as {current_pic} already registered",
                frontend_msg=f"{current_pic}さんが担当しています"
            )
        self.gcp_io.update_info(
            info_type=f"{registering_component}_PIC",
            cut_num=registering_cut,
            new_value=registering_person
        )
        self.gcp_io.color_cell(
            info_type=f"{registering_component}_PIC",
            cut_num=registering_cut,
            target_color=(0.7, 0.85, 0.85)
        )