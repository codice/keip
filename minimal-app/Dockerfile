FROM eclipse-temurin:21-jre
COPY target/minimal-app-0.4.0.jar /app/app.jar
VOLUME /var/spring/xml
VOLUME /var/spring/config
ENTRYPOINT ["java", "-Djdk.httpclient.HttpClient.log=errors,requests", "-Dspring.config.location=/var/spring/config/", "-jar", "/app/app.jar"]
