package com.project.demo.Model;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name="TB_CHAT")
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class Chat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "CHAT_IDX")
    private Integer chatIdx; // 채팅 식별자

    // fetch = FetchType.LAZY => 지연 로딩 방식,
    // chat 객체를 불러와도 실제
    @ManyToOne(fetch = FetchType.LAZY) // ManyToOne 관계
    @JoinColumn(name = "CROOM_IDX", nullable = false)
    private ChatRoom chatRoom; // 채팅방 식별자 외래키(ChatRoom)

    @Column(name = "CHATTER", nullable = false, length = 20)
    private String chatter; // 발화자

    @Column(name = "CHAT", columnDefinition = "TEXT")
    private String chat; // 채팅 내용

    @Column(name = "RATINGS", length = 1)
    private String ratings; // 채팅 평가 점수

    @Column(name = "CREATED_AT", nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now(); // 채팅보낸 시간
}
