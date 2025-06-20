package com.project.demo.Repository;

import com.project.demo.Model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Integer> {

     // Optional<User>은 값이 없을 수도 있다는 걸 명시
     Optional<User> findByUserEmailAndUserPwd(String userEmail, String userPwd);

     // user 이메일 중복체크해서 boolean 반환
     boolean existsByUserEmail(String userEmail);

}
