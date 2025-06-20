package com.project.demo.Controller;

import com.project.demo.Model.User;
import com.project.demo.Service.UserService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.function.BinaryOperator;

@Controller
public class UserController {

    // 로그린 화면 들어갈때
    @GetMapping("/")
    public String login() {
        return "login";
    }

    // 회원 가입 페이지로 이동
    @GetMapping("/sign")
    public String sign() {
        return "signup";
    }


}
