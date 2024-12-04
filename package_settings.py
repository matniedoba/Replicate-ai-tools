# This example demonstrates how to create a simple dialog in Anchorpoint
import anchorpoint as ap
import os

def apply_callback(dialog: ap.Dialog):
    token = dialog.get_value("token")  
    if(token==""):
        ap.UI().show_error("No token entered", "Please enter a valid API token")
    else:
        os.environ["REPLICATE_API_TOKEN"] = token
        ap.UI().show_success("Token Updated", "The token has been stored in your system environment")
        dialog.close()


def main():
    # Create a dialog container
    dialog = ap.Dialog()
    dialog.title = "Replicate Settings"
    ctx = ap.get_context()
    if ctx.icon:
        dialog.icon = ctx.icon

    dialog.add_text("<b>API Token</b>")

    token = os.environ["REPLICATE_API_TOKEN"]

    dialog.add_input(token,var="token", width=400, placeholder="45jdh5k3kjdh5k3jh54kjh3...",password=True)
    dialog.add_info("An API token is an identifier (similar to username and password), that<br>allows you to access the AI-cloud services from Replicate. Create an<br>API Token on <a href='https://replicate.com/account/api-tokens'>their website</a>. You will need to set up billing first.")

    dialog.add_button("Apply", callback=apply_callback)
    dialog.show()

if __name__ == "__main__":
    main()
