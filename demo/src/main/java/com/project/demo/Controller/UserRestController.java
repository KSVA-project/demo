package com.project.demo.Controller;

import com.project.demo.Model.User;
import com.project.demo.Service.UserService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
public class UserRestController {

    @Autowired
    private UserService userService;

    // 로그인 로직
    @PostMapping("/login")
    public ResponseEntity<Boolean> login(@RequestBody User user, HttpSession session) {

        String email = user.getUserEmail();
        String password = user.getUserPwd();

        System.out.println(email);
        System.out.println(password);

        User result = userService.login(email, password);

        // 유효성 체크
        if (result != null){
            session.setAttribute("user", user);
            return ResponseEntity.ok(true);
        } else {
            return ResponseEntity.status(401).body(false);
        }
    }


    // 회원 가입
    @PostMapping("/signup")
    public Boolean singUp(@RequestBody User user) {

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
