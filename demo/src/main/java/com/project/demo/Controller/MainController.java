package com.project.demo.Controller;

import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

import java.net.URI;

@Controller
public class MainController {

    // 로그인
    @GetMapping("/main")
    public String main() {
        return "main";
    }

    @GetMapping("/logout")
    public ResponseEntity<Void> logout(HttpSession session) {
        session.invalidate(); // 세션 무효화

        HttpHeaders headers = new HttpHeaders();

        headers.setCacheControl("no-cache, no-store, must-revalidate");
        // 캐싱 방지 설정

        headers.setPragma("no-cache");
        // HTTP/1.0 호환용 캐시 방지 헤더 (legacy 지원)

        headers.setExpires(0);
        // 응답이 즉시 만료된 것처럼 설정 → 역시 캐싱 방지 목적

        headers.setLocation(URI.create("/")); // 홈으로 리디렉트

        return new ResponseEntity<>(headers, HttpStatus.SEE_OTHER);
        // HttpStatus.SEE_OTHER → HTTP 303 status code (리디렉트)
        // 의미: "다른 URI로 요청을 다시하세요"
        // 브라우저가 자동으로 /로 리디렉트
    }
}
