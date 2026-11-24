package it.comune.trieste.ouf.semantic.application;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

@ConfigurationProperties("ouf.semantic.discovery-capacity")
public record ProviderCapacityProfile(
    @DefaultValue("default") String installationId,
    @DefaultValue("SCHEMA_GOV_IT") String logicalProviderId,
    @DefaultValue("1") String profileVersion,
    @DefaultValue("1") int providerSlots,
    @DefaultValue("1") int installationProviderInFlight,
    @DefaultValue("60") int slotMaxSeconds,
    @DefaultValue("300") int reconciliationTimeoutSeconds,
    @DefaultValue("30") int slotWaitMaxSeconds) {
  public ProviderCapacityProfile {
    if (!identifier(installationId) || !identifier(logicalProviderId) || !identifier(profileVersion)
        || providerSlots != 1 || installationProviderInFlight < 1 || installationProviderInFlight > 32
        || slotMaxSeconds < 1 || slotMaxSeconds > 120 || reconciliationTimeoutSeconds < slotMaxSeconds
        || reconciliationTimeoutSeconds > 86400 || slotWaitMaxSeconds < 1 || slotWaitMaxSeconds > 120)
      throw new IllegalArgumentException("DISCOVERY_CAPACITY_CONFIG_INVALID");
  }
  static ProviderCapacityProfile defaults() {
    return new ProviderCapacityProfile("default","SCHEMA_GOV_IT","1",1,1,60,300,30);
  }
  private static boolean identifier(String value) {
    return value != null && value.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,63}");
  }
}
