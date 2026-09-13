import SwiftUI

@main
struct DuoSampleApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    private let cards = [
        ("Plan", "Review the migration plan", "checkmark.circle.fill"),
        ("Build", "Compile for iPhone Duo", "hammer.fill"),
        ("Verify", "Inspect the rendered screen", "eye.fill")
    ]

    var body: some View {
        // Deliberately fragile examples for DuoPilot to find and repair.
        GeometryReader { _ in
            ZStack {
                Color.indigo
                    .ignoresSafeArea()

                VStack(spacing: 20) {
                    Text("DuoPilot")
                        .font(.largeTitle.bold())
                        .foregroundStyle(.white)

                    Text("A sample screen with fixed assumptions")
                        .font(.subheadline)
                        .foregroundStyle(.white.opacity(0.8))

                    VStack(spacing: 12) {
                        ForEach(cards, id: \.0) { card in
                            HStack(spacing: 14) {
                                Image(systemName: card.2)
                                    .frame(width: 30)
                                VStack(alignment: .leading) {
                                    Text(card.0).font(.headline)
                                    Text(card.1).font(.caption)
                                }
                                Spacer()
                            }
                            .padding()
                            .background(.white, in: RoundedRectangle(cornerRadius: 12))
                        }
                    }
                    .frame(width: UIScreen.main.bounds.width - 40)

                    Button("Continue") {}
                        .buttonStyle(.borderedProminent)
                        .tint(.white)
                        .foregroundStyle(.indigo)
                        .frame(width: 280, height: 52)
                }
                .frame(width: UIScreen.main.bounds.width)
            }
        }
    }
}
