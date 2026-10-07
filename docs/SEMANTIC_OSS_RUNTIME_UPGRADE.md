# Open source runtime upgrade for national discovery

Candidate only; not installed. The operator selected the open source route on 2026-10-07 after the exact discovery build failed its Critical/High threshold.

Spring Boot 4.1.1 manages Spring Framework 7.0.9, Spring Security 7.1.1, Tomcat 11.0.24 and PostgreSQL JDBC 42.7.13. Jackson 2 is pinned to 2.21.7 for the existing shared Authorization SDK and receipt/JSON contracts; Boot's deprecated Jackson 2 compatibility module and preferred converter are explicit. The Jackson 3 web starter is excluded from the production dependency path. Removing this temporary compatibility requires a coordinated SDK/contract migration.

Flyway and Micrometer use the explicit Boot 4 starters. MockMvc tests use the Boot 4 package. Existing migrations and owner authorization behavior remain subject to actual regression testing, not source-only assurance. Apache Thrift is pinned to 0.24.0 to correct the installed Jena transitive dependency findings.

No findings are ignored or relabelled. The new image must be built, scanned with the retained fresh database and accepted with the coordinated installation before deployment. User choice is not a release acceptance or semantic publication approval.

References: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide and https://spring.io/security/cve-2026-47884/.
