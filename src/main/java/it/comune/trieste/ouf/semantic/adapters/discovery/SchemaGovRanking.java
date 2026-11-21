package it.comune.trieste.ouf.semantic.adapters.discovery;

import com.fasterxml.jackson.databind.JsonNode;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider.Query;
import java.util.*;
import java.util.regex.Pattern;

final class SchemaGovRanking {
  record Match(String uri,double score,String label,String language,String reason) {
    List<String> reasons(){
      String source=label.isEmpty()?"schema.gov.it SPARQL match":"label: "+label+(language.isEmpty()?"":" ["+language+"]");
      return List.of(source,reason+" (score "+score+")");
    }
  }

  private static final Pattern SPACES=Pattern.compile("(?U)\\s+");
  private static final Comparator<Match> ORDER=Comparator.comparingDouble(Match::score).reversed()
      .thenComparing(Match::uri).thenComparing(Match::label).thenComparing(Match::language);

  static List<Match> rank(JsonNode rows,Query query){
    if(rows.size()>50)throw new BoundedGatewayClient.ProviderFailure("SCHEMA_GOV_SPARQL_RESULT_INVALID");
    String intent=normalize(query.intent());
    String compactIntent=intent.replace(" ","");
    Pattern word=Pattern.compile("(?U)(?<!\\w)"+Pattern.quote(intent)+"(?!\\w)");
    var matches=new ArrayList<Match>();
    for(JsonNode row:rows){
      String uri=row.path("resource").path("value").textValue();
      if(uri==null || uri.isBlank())throw new BoundedGatewayClient.ProviderFailure("SCHEMA_GOV_SPARQL_RESULT_INVALID");
      var binding=row.path("label");
      String label=binding.path("value").asText("");
      String language=binding.path("xml:lang").asText("").toLowerCase(Locale.ROOT);
      String normalized=normalize(label);
      int points;
      String reason;
      if(normalized.isEmpty()){points=20;reason="URI match";}
      else if(normalized.replace(" ","").equals(compactIntent)){points=95;reason="exact label";}
      else if(normalized.startsWith(intent)){points=80;reason="label prefix";}
      else if(word.matcher(normalized).find()){points=65;reason="whole word in label";}
      else if(normalized.contains(intent)){points=50;reason="substring in label";}
      else {points=20;reason="provider match";}
      // Requests accept at most five ordered language preferences. Quality always wins.
      int index=query.preferredLanguages().indexOf(language);
      if(index>=0 && index<5 && !normalized.isEmpty()){
        points+=5-index;
        reason+=", preferred language "+language;
      }
      matches.add(new Match(uri,points/100.0,label,language,reason));
    }
    return matches.stream().sorted(ORDER).toList();
  }

  private static String normalize(String text){
    return SPACES.matcher(text).replaceAll(" ").strip().toLowerCase(Locale.ROOT);
  }
}
