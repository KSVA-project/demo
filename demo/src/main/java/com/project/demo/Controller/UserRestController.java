package com.project.demo.Controller;

import com.project.demo.Model.User;
import com.project.demo.Service.UserService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
public class UserRestController {

    @Autowired
    private UserService userService;

    // 로그인 로직
    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody User user, HttpSession session) {

        String email = user.getUserEmail();
        String password = user.getUserPwd();

        User result = userService.login(email, password);

        // 유효성 체크
        if (result != null) {
            session.setAttribute("userIdx", result.getUserIdx());
            session.setAttribute("userName", result.getUserName());

            // 프론트로도 응답
            Map<String, Object> response = new HashMap<>();
            response.put("userIdx", result.getUserIdx());
            response.put("userName", result.getUserName());

            return ResponseEntity.ok(response);
        } else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
    }

    // 회원 가입
    @PostMapping("/signup")
    public Boolean signUp(@RequestBody User user) {

        boolean result = userService.register(user);
        return result;
    }

    // 이메일 유효성 체크
    @GetMapping("/check-email")
    public ResponseEntity<Boolean> checkEmail(@RequestParam String userEmail) {
        boolean exists = userService.isEmailExists(userEmail);
        return ResponseEntity.ok(exists);
    }

}
