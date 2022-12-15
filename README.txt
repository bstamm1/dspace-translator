> DSpace Translator

This python script translates the contents of a DSpace collection using
google's translation API.



> Install python requirements

>
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
>



> Install DSpace with Docker

Clone the dspace angular repository.

>
mkdir Code/dspace
cd Code/dspace
git clone https://github.com/DSpace/dspace-angular.git
cd dspace-angular
>

Install docker desktop for mac:

Follow instructions here: https://docs.docker.com/desktop/install/mac-install/

Verify that docker and docker-compose are installed.

>
docker --version
docker compose --version
>

Follow instructions to install dspace with docker. https://github.com/DSpace/dspace-angular/blob/main/docker/README.md

>
docker compose -p d7 -f docker/docker-compose.yml -f docker/docker-compose-rest.yml up
>

You should now be able to access dspace at "localhost:4000" in your browser.

Now create an admin user in a separate terminal (<ctrl+t> to create a new tab).

>
docker compose -p d7 -f docker/cli.yml run --rm dspace-cli create-administrator -e test@test.edu -f admin -l user -p admin -c en
>




> Create A Google Cloud Account

Install the gcloud CLI to authenticate with google translate APIs.

https://cloud.google.com/sdk/docs/install
