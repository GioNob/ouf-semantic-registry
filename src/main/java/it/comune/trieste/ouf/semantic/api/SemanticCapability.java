package it.comune.trieste.ouf.semantic.api;
import java.lang.annotation.*;
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
public @interface SemanticCapability {String value();}
