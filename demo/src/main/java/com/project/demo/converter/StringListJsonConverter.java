package com.project.demo.converter;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

import java.util.Collections;
import java.util.List;

// 이 클래스가 JPA에서 사용할 수 있는 변환기임을 선언
@Converter
public class StringListJsonConverter implements AttributeConverter<List<String>, String> {
    // implements AttributeConverter<X, Y>:
    // X: Java 객체 타입 (List<String>)
    // Y: DB에 저장될 타입 (String)

    private final ObjectMapper objectMapper = new ObjectMapper();
    // ObjectMapper는 Jackson 라이브러리에서 제공하는 클래스
    // Java 객체와 JSON 간 변환을 도와주는 도구

    // writeValueAsString()	자바 객체 → JSON 문자열
    // readValue()	JSON 문자열 → 자바 객체
    
    // List<String>을 JSON 문자열로 변환해 DB에 저장
    @Override
    public String convertToDatabaseColumn(List<String> attribute) {
        try {
            return objectMapper.writeValueAsString(attribute);
            // objectMapper.writeValueAsString(attribute)
            // JPA가 insert/update 쿼리를 만들 때, 이 메서드를 호출해서 DB에 들어갈 문자열로 만듦

        } catch (Exception e) {
            return "[]";
        }
    }

    // DB에서 가져온 JSON 문자열을 List<String>으로 복원
    @Override
    public List<String> convertToEntityAttribute(String dbData) {
        try {
            return objectMapper.readValue(dbData, new TypeReference<List<String>>() {});
            // DB에서 데이터를 조회해서 Java 객체(Entity)로 복원할 때 자동 실행

        } catch (Exception e) {
            return Collections.emptyList();
        }
    }
}
