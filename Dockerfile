FROM python:3.6
RUN apt-get update && apt-get -y install libyajl-dev
ENV PIPENV_VENV_IN_PROJECT=1
RUN pip install pipenv
WORKDIR /tinman
ADD Pipfile Pipfile.lock /tinman/
RUN pipenv install
ADD . /tinman/
ENTRYPOINT ["pipenv", "run", "python", "-m", "tinman"]
