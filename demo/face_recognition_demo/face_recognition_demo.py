import face_recognition

donald_image = face_recognition.load_image_file("donald_trump.jpg")

donald_face_location = face_recognition.face_locations(donald_image)
print("\nDonald face location:")
print(donald_face_location)

donald_face_landmarks = face_recognition.face_landmarks(donald_image)
print("\nDonald face landmarks:")
print(donald_face_landmarks)

friends_image = face_recognition.load_image_file("donald_trump_and_friends.jpg")

friends_face_locations = face_recognition.face_locations(friends_image)
print("\nDonald's friends faces location:")
print(friends_face_locations)

friends_face_landmarks = face_recognition.face_landmarks(friends_image)
print("\nDonald's friends faces landmarks:")
print(friends_face_landmarks)

donald_encoding = face_recognition.face_encodings(donald_image)[0]
print("\nDonald face encoding:")
print(donald_encoding)

friends_encoding = face_recognition.face_encodings(friends_image)

comparison_results = face_recognition.compare_faces(friends_encoding, donald_encoding)
print("\nComparison results:")
print(comparison_results)
