-- phpMyAdmin SQL Dump
-- version 5.2.1
-- Database: `quietqueue`

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `full_name`, `email`, `password`, `created_at`) VALUES
(1, 'Rithwika', 'rithwika.mode@gmail.com', 'scrypt:32768:8:1$9953Vj2zIR5rzDYh$6cae44caa957628b8add11e0f42a35e46ae3b7e9b5903258ea522fe77942b228f5032c2f9fde350f1435bc9e7a169791a49254e53d8601076d13ee34ce1d49cb', '2025-10-29 19:42:52');

-- --------------------------------------------------------

--
-- Table structure for table `announcements`
--

CREATE TABLE `announcements` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` text NOT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `announcements`
--

INSERT INTO `announcements` (`id`, `title`, `message`, `created_by`, `created_at`) VALUES
(12, 'sdf', 'asdfg', 1, '2025-11-05 19:42:01'),
(14, 'Maintenance', 'The library will be closed from 9 AM to 12 PM tomorrow for maintenance.', 1, '2025-11-06 09:56:05'),
(15, 'Announcement', 'Testing', 1, '2025-11-06 10:32:39');

-- --------------------------------------------------------

--
-- Table structure for table `bookings`
--

CREATE TABLE `bookings` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `seat_id` varchar(64) NOT NULL,
  `zone` varchar(64) DEFAULT NULL,
  `booking_date` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `status` enum('reserved','checked_in','completed','cancelled') NOT NULL DEFAULT 'reserved',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `checked_in_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bookings`
--

INSERT INTO `bookings` (`id`, `user_id`, `seat_id`, `zone`, `booking_date`, `start_time`, `end_time`, `status`, `created_at`, `checked_in_at`) VALUES
(21, 7, 'A_1', 'zone1', '2025-11-06', '14:30:00', '15:30:00', 'cancelled', '2025-11-06 13:17:16', NULL),
(22, 7, 'A_2', 'zone1', '2025-11-06', '13:23:40', '13:34:08', '', '2025-11-06 13:23:40', '2025-11-06 13:23:40'),
(24, 5, 'A_6', 'zone1', '2025-11-06', '16:30:00', '18:30:00', 'cancelled', '2025-11-06 14:01:12', NULL),
(25, 7, 'A_4', 'zone1', '2025-11-06', '16:30:00', '18:30:00', 'cancelled', '2025-11-06 14:03:41', NULL),
(26, 8, 'A_2', 'zone1', '2025-11-06', '14:12:18', '14:19:32', '', '2025-11-06 14:12:18', '2025-11-06 14:12:18'),
(27, 8, 'A_2', 'zone1', '2025-11-06', '14:21:58', '15:21:58', '', '2025-11-06 14:21:58', '2025-11-06 14:21:58'),
(28, 7, 'B_5', 'zone2', '2025-11-06', '20:30:00', '22:30:00', 'cancelled', '2025-11-06 16:38:58', NULL),
(29, 9, 'B_4', 'zone2', '2025-11-06', '18:00:00', '19:00:00', 'cancelled', '2025-11-06 17:12:21', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `books`
--

CREATE TABLE `books` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `author` varchar(100) DEFAULT NULL,
  `isbn` varchar(50) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `total_copies` int(11) DEFAULT 1,
  `available_copies` int(11) DEFAULT 1,
  `added_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `books`
--

INSERT INTO `books` (`id`, `title`, `author`, `isbn`, `category`, `total_copies`, `available_copies`, `added_at`) VALUES
(11, 'Engineering Physics', 'EP', '1234', 'IT', 30, 30, '2025-11-05 20:06:37'),
(12, 'Linear Algebra', 'LAL', '125', 'ECE', 24, 12, '2025-11-05 20:07:08'),
(13, 'FinTech', 'FT', '789', 'IT-BI', 15, 14, '2025-11-05 20:07:50'),
(14, 'Theory Of Computation', 'TOC', '567', 'IT', 34, 31, '2025-11-06 08:35:27'),
(15, 'Probability', 'PS', '345', 'IT', 56, 32, '2025-11-06 08:36:02'),
(16, 'Operating System', 'OS', '654', 'IT', 54, 34, '2025-11-06 08:37:02'),
(17, 'Software Engineering', 'SE', '835', 'IT', 73, 68, '2025-11-06 08:37:30');

-- --------------------------------------------------------

--
-- Table structure for table `book_issues`
--

CREATE TABLE `book_issues` (
  `id` int(11) NOT NULL,
  `student_id` int(11) NOT NULL,
  `book_id` int(11) NOT NULL,
  `issue_date` date NOT NULL,
  `return_date` date DEFAULT NULL,
  `status` enum('issued','returned') DEFAULT 'issued'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `password_resets`
--

CREATE TABLE `password_resets` (
  `id` int(11) NOT NULL,
  `email` varchar(100) NOT NULL,
  `token` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `seats`
--

CREATE TABLE `seats` (
  `seat_id` int(11) NOT NULL,
  `zone` varchar(50) NOT NULL,
  `seat_number` int(11) NOT NULL,
  `is_booked` tinyint(1) DEFAULT 0,
  `booked_by` int(11) DEFAULT NULL,
  `booked_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `students`
--

CREATE TABLE `students` (
  `id` int(11) NOT NULL,
  `roll_number` varchar(20) DEFAULT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `course` varchar(50) DEFAULT NULL,
  `semester` varchar(10) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT 0,
  `photo` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students`
--

INSERT INTO `students` (`id`, `roll_number`, `full_name`, `email`, `course`, `semester`, `password`, `is_admin`, `photo`) VALUES
(5, 'IIT2024254', 'Sravanthi', 'iit2024254@iiita.ac.in', 'B.Tech', '3', 'scrypt:32768:8:1$W55rphvrXTz855go$e00357841d5f9335ce0a8db95366d76fe66f9644ca27ea2d16f2e2801b4e48853b5aa013909b6244fbca853caf9d01e8b2523408fb02a2b854087fff25d4e414', 0, NULL),
(7, 'IIB2024021', 'Mode Rithwika Naidu', 'iib2024021@iiita.ac.in', 'B.Tech', '3', 'scrypt:32768:8:1$KNwTvZJJNgz5Ebxc$a32d72cd7f373af21de204bda6eab904c3dea84303e2ea9104c2e2e7ecf90839896d5ad62ef46435bbfa82629e665659dfe09b378c1433c22c05a5e023c0b437', 0, 'user_7_addition result.png'),
(8, 'IIT2024104', 'Sadhvika N', 'iit2024104@iiita.ac.in', 'B.Tech', '3', 'scrypt:32768:8:1$qRBNE6K7S7MmQ1JK$71b8a8071c32ea14b8f31199455cc18a221a126e7d4dfcb2d7baca14a8dc8298701db9edbb2cd8bc7057d3a9c242f4aac5eec95d9da023da77f3f05ba508e968', 0, NULL),
(9, 'IIB2024007', 'Kavya', 'iib2024007@iiita.ac.in', 'B.Tech', '3', 'scrypt:32768:8:1$kYCkqYJCx0UPLEDs$fa8664478a34e64d4dafd0bfcb125a456fa9b12dcde57343b80a2dc6833e217121919398cff6920459b91b4049edc4bf54f47aa1bbff76ff1ae5f0b314a36fb5', 0, NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `announcements`
--
ALTER TABLE `announcements`
  ADD PRIMARY KEY (`id`),
  ADD KEY `created_by` (`created_by`);

--
-- Indexes for table `bookings`
--
ALTER TABLE `bookings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_seat_time` (`seat_id`,`booking_date`,`start_time`,`end_time`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `idx_date` (`booking_date`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_bookings_datetime` (`booking_date`,`start_time`,`status`);

--
-- Indexes for table `books`
--
ALTER TABLE `books`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `isbn` (`isbn`);

--
-- Indexes for table `book_issues`
--
ALTER TABLE `book_issues`
  ADD PRIMARY KEY (`id`),
  ADD KEY `student_id` (`student_id`),
  ADD KEY `book_id` (`book_id`);

--
-- Indexes for table `password_resets`
--
ALTER TABLE `password_resets`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `seats`
--
ALTER TABLE `seats`
  ADD PRIMARY KEY (`seat_id`),
  ADD KEY `booked_by` (`booked_by`);

--
-- Indexes for table `students`
--
ALTER TABLE `students`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `announcements`
--
ALTER TABLE `announcements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT for table `bookings`
--
ALTER TABLE `bookings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=30;

--
-- AUTO_INCREMENT for table `books`
--
ALTER TABLE `books`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `book_issues`
--
ALTER TABLE `book_issues`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `password_resets`
--
ALTER TABLE `password_resets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `seats`
--
ALTER TABLE `seats`
  MODIFY `seat_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `students`
--
ALTER TABLE `students`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `announcements`
--
ALTER TABLE `announcements`
  ADD CONSTRAINT `announcements_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `admins` (`id`);

--
-- Constraints for table `bookings`
--
ALTER TABLE `bookings`
  ADD CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `students` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `book_issues`
--
ALTER TABLE `book_issues`
  ADD CONSTRAINT `book_issues_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`),
  ADD CONSTRAINT `book_issues_ibfk_2` FOREIGN KEY (`book_id`) REFERENCES `books` (`id`);

--
-- Constraints for table `seats`
--
ALTER TABLE `seats`
  ADD CONSTRAINT `seats_ibfk_1` FOREIGN KEY (`booked_by`) REFERENCES `students` (`id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;