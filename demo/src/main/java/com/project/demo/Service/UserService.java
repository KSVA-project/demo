package com.project.demo.Service;

import com.project.demo.Model.User;
import com.project.demo.Repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;

    // 로그인
    public User login(String email, String password) {
        return userRepository.findByUserEmailAndUserPwd(email, password).orElse(null);
    }

    // 회원가입
    public boolean register(User user) {
        try {
            userRepository.save(user);
            return true;

        } catch (Exception e) {
            return false;
        }
    }

    // 이메일 중복체크
    public boolean isEmailExists(String userEmail) {
        return userRepository.existsByUserEmail(userEmail);
    }
}
