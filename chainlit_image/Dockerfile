FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.13-alpine3.21

# update the apk 
RUN apk upgrade --no-cache

# add build-base for gcc compiler
RUN apk add --no-cache build-base

# add a new user and change to the new user
# this is done to do not run the container as Root
# Create a group and user
RUN addgroup -S chainlitworkergroup && adduser -S chainlitworker -G chainlitworkergroup
USER chainlitworker

# Set environment variables (e.g., set Python to run in unbuffered mode)
ENV PYTHONUNBUFFERED 1

# Set the working directory where user has access
WORKDIR /home/chainlitworker/app

# Copy your application with permission for the correct user
COPY  --chown=chainlitworker:chainlitworker ./foundational-llm-chat_app .

#install requirements --user for current owner
RUN pip install -U --user -r /home/chainlitworker/app/requirements.txt

#update path for using accessing libraries installed
ENV PATH="/home/chainlitworker/.local/bin:${PATH}"

EXPOSE 8080

CMD ["python", "-m", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8080"]