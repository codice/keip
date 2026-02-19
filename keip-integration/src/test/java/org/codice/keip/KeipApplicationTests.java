package org.codice.keip;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@TestPropertySource(properties = "keip.integration.filepath=classpath:test-route.xml")
class KeipApplicationTests {

    @Test
    void contextLoads() {}
}
