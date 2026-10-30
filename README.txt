War Shooter - GitHub Actions build files

Upload the CONTENTS of this folder to the ROOT of your GitHub repository.
Keep .github/workflows/android.yml at exactly that path.
Do not upload this ZIP as a single file.

Before running Actions, check for old workflow files under .github/workflows.
To avoid confusion, keep only android.yml while testing this setup.

This workflow explicitly installs Android SDK Build Tools and checks AIDL before building.
A successful APK is not guaranteed until the workflow finishes successfully; Pygame Android compatibility may cause later errors.
