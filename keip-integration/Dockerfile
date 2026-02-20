# Local development Dockerfile. CI releases use the Jib Maven plugin (see pom.xml).
FROM eclipse-temurin:21-jre@sha256:34a58218d838035428163eb35abb629944c5906d1bedcfef8bc8864cce11dfe5
RUN groupadd --system --gid 999 appgroup && useradd --system --uid 999 --gid appgroup appuser
COPY target/app.jar /app/app.jar
RUN chown -R 999:999 /app
USER 999
ENTRYPOINT ["java", "-Djdk.httpclient.HttpClient.log=errors,requests", "-Dspring.config.location=/var/spring/config/", "-jar", "/app/app.jar"]
