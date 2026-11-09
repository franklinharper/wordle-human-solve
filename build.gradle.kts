plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
    application
}

group = "com.franklinharper"
version = "0.1.0"

dependencies {
    implementation(libs.ktor.client.core)
    implementation(libs.ktor.client.cio)
    implementation(libs.ktor.client.content.negotiation)
    implementation(libs.ktor.serialization.kotlinx.json)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.clikt)
    implementation(libs.sqlite.jdbc)
    // Ktor logs via SLF4J; nop binding silences its "no provider" stderr noise.
    runtimeOnly(libs.slf4j.nop)
    testImplementation(libs.kotlin.test.junit5)
    testImplementation(libs.junit.jupiter.api)
    testRuntimeOnly(libs.junit.jupiter.engine)
}

application {
    mainClass = "com.franklinharper.wordle.MainKt"
}

tasks.test {
    useJUnitPlatform()
    // Tests and commands read the word lists from the repo root, which is
    // the Gradle project directory — make that explicit rather than
    // inheriting whatever directory the test JVM happens to start in.
    workingDir = rootProject.projectDir
}
