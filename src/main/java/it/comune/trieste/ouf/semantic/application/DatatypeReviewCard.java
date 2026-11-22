package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.*;

/** Italian projection of the revision bound to a HUMAN approval challenge. */
final class DatatypeReviewCard {
  private static final Map<String,String> TYPES=Map.of(
      "string","Testo", "integer","Numero intero", "decimal","Numero decimale",
      "boolean","Vero o falso", "date","Data", "datetime","Data e ora UTC",
      "geometry","Geometria", "concept","Concetto di un vocabolario pubblicato");
  private static final Map<String,String> CONSTRAINTS=Map.of(
      "minInclusive","Minimo incluso", "maxInclusive","Massimo incluso",
      "maxLength","Lunghezza massima", "vocabularyRef","Vocabolario");

  static Map<String,Object> build(JsonNode current,JsonNode previous) {
    var warnings=new ArrayList<String>();
    var rows=new ArrayList<Map<String,String>>();
    String label=current.path("label_json").path("it").asText("");
    String description=current.path("description_json").path("it").asText("");
    if(label.isBlank()) warnings.add("Manca l’etichetta italiana del tipo.");
    if(description.isBlank()) warnings.add("Manca la descrizione italiana del tipo.");
    var components=index(current);
    components.forEach((name,c)->{
      String componentLabel=c.path("labels").path("it").asText("");
      if(componentLabel.isBlank()) warnings.add("Il componente «"+name+"» è senza etichetta italiana.");
      String type=c.path("type").asText();
      var limits=new StringJoiner(", ");
      c.path("constraints").fields().forEachRemaining(e->
          limits.add(CONSTRAINTS.getOrDefault(e.getKey(),e.getKey())+" "+e.getValue().asText()));
      rows.add(Map.of("nome",name,"etichetta",componentLabel,"tipo",TYPES.getOrDefault(type,"Tipo strutturato pubblicato · "+type),
          "cardinalità","ONE".equals(c.path("cardinality").asText())?"Un valore":"Più valori",
          "obbligatorio",c.path("required").asBoolean()?"Sì":"No","vincoli",limits.length()==0?"Nessuno":limits.toString()));
    });

    var differences=new ArrayList<Map<String,Object>>();
    if(previous!=null) {
      var before=index(previous);
      for(String field:List.of("label_json","description_json"))
        diff(differences,"label_json".equals(field)?"Etichetta":"Descrizione",previous.path(field),current.path(field));
      var names=new LinkedHashSet<>(before.keySet());
      names.addAll(components.keySet());
      for(String name:names) diff(differences,name,before.get(name),components.get(name));
      var oldOrder=List.copyOf(before.keySet());
      var newOrder=List.copyOf(components.keySet());
      if(before.keySet().equals(components.keySet()) && !oldOrder.equals(newOrder))
        differences.add(Map.of("campo","Ordine dei componenti","modifica","Modificato","prima",oldOrder,"dopo",newOrder));
    }
    return Map.of("etichetta",label,"descrizione",description,"componenti",rows,"avvisi",warnings,
        "versionePrecedente",previous==null?"Prima pubblicazione":previous.path("semantic_version").asText(),
        "differenze",differences);
  }

  private static Map<String,JsonNode> index(JsonNode revision) {
    Map<String,JsonNode> byName=new LinkedHashMap<>();
    revision.path("definition_json").path("components").forEach(c->byName.put(c.path("name").asText(),c));
    return byName;
  }

  private static void diff(List<Map<String,Object>> differences,String field,JsonNode before,JsonNode after) {
    if(Objects.equals(before,after)) return;
    var change=new LinkedHashMap<String,Object>();
    change.put("campo",field);
    change.put("modifica",before==null?"Aggiunto":after==null?"Rimosso":"Modificato");
    if(before!=null) change.put("prima",before);
    if(after!=null) change.put("dopo",after);
    differences.add(change);
  }
}
