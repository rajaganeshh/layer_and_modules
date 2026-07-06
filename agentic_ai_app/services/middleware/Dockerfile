ARG BASE_IMAGE
FROM $BASE_IMAGE


# Copy the src folder from the build context into the image
ARG APPLICATION_NAME
COPY services/${APPLICATION_NAME}/src/package*.json /app/

WORKDIR /app

RUN npm cache clean --force && npm install --legacy-peer-deps
 
COPY services/${APPLICATION_NAME}/src/ /app/
 
#Build reactapp
RUN pwd && ls -ltr *

EXPOSE 80
 
# CMD [ "npm","start" ]
 
CMD ["node", "index.js"]
# CMD pm2 start index.js -i 1 --name "container_name" & tail -f /dev/null

