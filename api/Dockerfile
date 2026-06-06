# Usar uma imagem base oficial do OpenJDK para o Java 17 com Maven
FROM ubuntu:latest

# Instalar OpenJDK 17 e Maven
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk maven && \
    rm -rf /var/lib/apt/lists/*

# Definir o diretório de trabalho no contêiner
WORKDIR /app

# Copiar os arquivos do projeto Spring Boot
COPY . .

# Construir o projeto Maven. Isso irá gerar o JAR executável.
RUN mvn clean package -Dmaven.test.skip=true

# O JAR executável estará em target/kizuna-copilot-0.0.1-SNAPSHOT.jar (ou similar, conforme a versão no pom.xml)
# Precisamos descobrir o nome exato do JAR ou usar um padrão.
# Por simplicidade, vamos assumir o nome padrão ou ajustar posteriormente.

# Expor a porta que a aplicação Spring Boot irá usar (padrão é 8080)
EXPOSE 8080

# Comando para executar a aplicação Spring Boot
# Encontra o JAR gerado no diretório target/ e o executa.
CMD ["java", "-jar", "target/kizuna-copilot-0.0.1-SNAPSHOT.jar"]
