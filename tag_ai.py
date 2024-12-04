# This example demonstrates how to create a simple dialog in Anchorpoint
import anchorpoint as ap
import apsync as aps
import os
import tempfile
import replicate
import random


def get_thumbnail_image(workspace_id, input_path):
    # create temporary folder
    output_folder = create_temp_directory()

    # generate the thumbnail which is a png file and put it in the temporary directory
    aps.generate_thumbnails(
        [input_path],
        output_folder,
        with_detail=True,
        with_preview=False,
        workspace_id=workspace_id,
    )

    # get the proper filename, rename it because the generated PNG file has a _pt appendix
    file_name = os.path.basename(input_path).split(".")[0]
    image_path = os.path.join(
        output_folder, file_name + str("_dt") + str(".png"))

    return image_path


def create_temp_directory():
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    return temp_dir


def ai_tag(input_path):

    # Check if the file exists
    if os.path.exists(input_path):
        with open(input_path, "rb") as file_input:  # Open the file in binary mode
            input = {
                "input_image": file_input  # Pass the file object directly
            }

            output = replicate.run(
                "idea-research/ram-grounded-sam:80a2aede4cf8e3c9f26e96c308d45b23c350dd36f1c381de790715007f1ac0ad",
                input=input
            )
            return output
    else:
        raise FileNotFoundError(f"The file at {input_path} does not exist.")


def process_images(workspace_id, input_paths, database, attribute):
    # start progress
    progress = ap.Progress("Generating Tags", "Processing", infinite=True)
    allowed_extensions = [
        "psd",
        "exr",
        "tga",
        "obj",
        "fbx",
        "glb",
        "gltf",
        "hdr",
        "png",
        "jpg",
        "tga"
    ]

    # Loop through each input path
    for input_path in input_paths:
        # Check if the input_path has an allowed extension
        if not any(input_path.lower().endswith(ext) for ext in allowed_extensions):
            print(
                f"Skipping {input_path} as it does not have an allowed extension.")
            continue
        image_path = input_path
        # Get the file name from the path
        file_name = os.path.basename(input_path)
        # check if thumbnail generation is needed
        bypass_thumbnail_filetypes = ["jpg", "png", "tga"]
        if input_path.split(".")[-1].lower() not in bypass_thumbnail_filetypes:
            # Show only the file name
            progress.set_text(f"Generating proxy image for {file_name}")
            image_path = get_thumbnail_image(workspace_id, input_path)

            if not os.path.exists(image_path):
                ap.UI().show_error(
                    "Cannot process image", "PNG file could not be generated"
                )
                progress.finish()
                return

        # Show only the file name
        progress.set_text(
            f"Requesting tags from Replicate for {file_name}. This can take some time.")
        try:
            output = ai_tag(image_path)

            # Extracting tags and creating a new list variable
            image_tags = output['json_data']['tags'].split(
                ', ') + output['tags'].split(', ')
            # Removing duplicates by converting to a set and back to a list
            image_tags = list(set(image_tags))
        except Exception as e:
            # Show only the file name
            error_message = str(e)
            print(f"Error processing AI tags for {file_name}: {error_message}")
            if "status: 401" in error_message and "Invalid token" in error_message:
                ap.UI().show_error("Something went wrong", "Your API token is not working. You have to get a new token from Replicate and paste it in the Action settings.")
            else:
                ap.UI().show_error("Something went wrong", "Open the console for more information")
            progress.finish()
            return

        anchorpoint_tags = attribute.tags

        colors = ["grey", "blue", "purple", "green",
                  "turk", "orange", "yellow", "red"]

        # Create a set of anchorpoint tag names for faster lookup
        anchorpoint_tag_names = {tag.name for tag in anchorpoint_tags}

        # Add new tags from image_tags that are not already in anchorpoint_tag_names
        for image_tag in image_tags:
            if image_tag not in anchorpoint_tag_names:
                new_tag = aps.AttributeTag(image_tag, random.choice(colors))
                anchorpoint_tags.append(new_tag)

        # Update the attribute tags in the database
        database.attributes.set_attribute_tags(attribute, anchorpoint_tags)

        # Create a list of file tags based on the updated anchorpoint tags
        file_tags = aps.AttributeTagList()
        for anchorpoint_tag in anchorpoint_tags:
            if anchorpoint_tag.name in image_tags:
                file_tags.append(anchorpoint_tag)

        # Set the attribute value for the input path
        database.attributes.set_attribute_value(
            input_path, attribute, file_tags)

    progress.finish()


def main():
    ctx = ap.get_context()
    database = ap.get_api()
    # Create or get the "AI Tags" attribute
    attribute = database.attributes.get_attribute("AI-Tags")
    if not attribute:
        attribute = database.attributes.create_attribute(
            "AI-Tags", aps.AttributeType.multiple_choice_tag
        )
    ctx.run_async(process_images, ctx.workspace_id,
                  ctx.selected_files, database, attribute)


if __name__ == "__main__":
    main()
