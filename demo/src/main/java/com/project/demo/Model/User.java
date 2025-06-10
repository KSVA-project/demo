package com.project.demo.Model;


import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "TB_USER")
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class User {

    @Id // PRIMARY KEY
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "USER_IDX")
    private Integer userIdx;

    @Column(name = "USER_EMAIL", nullable = false, length = 50)
    private String userEmail;

    @Column(name = "USER_PWD", nullable = false, length = 50)
    private String userPwd;

    @Column(name = "USER_NAME", nullable = false, length = 200)
    private String userName;

    @Column(name = "CREATED_AT", nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    private List<ChatRoom> chatRooms;

}
